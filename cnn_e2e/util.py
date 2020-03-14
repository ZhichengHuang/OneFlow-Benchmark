from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import time
import numpy as np
import pandas as pd
from datetime import datetime
import oneflow as flow


def InitNodes(args):
    if args.num_nodes > 1:
        assert args.num_nodes <= len(args.node_ips)
        nodes = []
        for n in args.node_list.strip().split(","):
            addr_dict = {}
            addr_dict["addr"] = n
            nodes.append(addr_dict)

        flow.env.machine(nodes)


class Snapshot:
    def __init__(self, model_save_dir, model_load_dir):
        self._model_save_dir = model_save_dir
        self._check_point = flow.train.CheckPoint()
        if model_load_dir:
            assert os.path.isdir(model_load_dir)
            print("Restoring model from {}.".format(model_load_dir))
            self._check_point.load(model_load_dir)
        else:
            print("Init model on demand.")
            self._check_point.init()

    def save(self, name):
        snapshot_save_path = os.path.join(self._model_save_dir, "snapshot_{}".format(name))
        if not os.path.exists(snapshot_save_path):
            os.makedirs(snapshot_save_path)
        print("Saving model to {}.".format(snapshot_save_path))
        self._check_point.save(snapshot_save_path)


class Summary():
    def __init__(self, log_dir, config):
        self._log_dir = log_dir
        self._metrics = pd.DataFrame({"iter": 0, "legend": "cfg", "note": str(config)}, index=[0])

    def scalar(self, legend, value, step=-1):
        # TODO: support rank(which device/gpu)
        df = pd.DataFrame(
            {"iter": step, "legend": legend, "value": value, "rank": 0, "time": time.time()},
            index=[0])
        self._metrics = pd.concat([self._metrics, df], axis=0, sort=False)

    def save(self):
        save_path = os.path.join(self._log_dir, "summary.csv")
        self._metrics.to_csv(save_path, index=False)
        print("saved: {}".format(save_path))


class StopWatch:
    def __init__(self):
        pass

    def start(self):
        self.start_time = time.time()
        self.last_split = self.start_time

    def split(self):
        now = time.time()
        duration = now - self.last_split
        self.last_split = now
        return duration

    def stop(self):
        self.stop_time = time.time()

    def duration(self):
        return self.stop_time - self.start_time


def match_top_k(predictions, labels, top_k=1):
    max_k_preds = predictions.argsort(axis=1)[:, -top_k:][:, ::-1]
    match_array = np.logical_or.reduce(max_k_preds==labels.reshape((-1, 1)), axis=1)
    num_matched = match_array.sum()
    #topk_acc_score = match_array.sum().astype(float) / match_array.shape[0]
    return num_matched, match_array.shape[0]

class Metric():
    def __init__(self, desc='train', calculate_batches=-1, batch_size=256, top_k=5,
                 prediction_key='predictions', label_key='labels', loss_key=None):
        self.desc = desc
        self.calculate_batches = calculate_batches
        self.top_k = top_k
        self.prediction_key = prediction_key
        self.label_key = label_key
        self.loss_key = loss_key
        if loss_key:
            self.fmt = "{}: epoch {}, iter {}, loss: {:.6f}, top_1: {:.6f}, top_k: {:.6f}, samples/s: {:.3f}"
        else:
            self.fmt = "{}: epoch {}, iter {}, top_1: {:.6f}, top_k: {:.6f}, samples/s: {:.3f}"

        self.timer = StopWatch()
        self.timer.start()
        self._clear()
    
    def _clear(self):
        self.top_1_num_matched = 0
        self.top_k_num_matched = 0
        self.num_samples = 0.0

    def metric_cb(self, epoch, step):
        def callback(outputs):
            if step == 0: self._clear()
            num_matched, num_samples = match_top_k(outputs[self.prediction_key], 
                                                   outputs[self.label_key])
            self.top_1_num_matched += num_matched 
            self.num_samples += num_samples
            num_matched, _ = match_top_k(outputs[self.prediction_key], 
                                         outputs[self.label_key], self.top_k)
            self.top_k_num_matched += num_matched 

            if (step+1) % self.calculate_batches == 0:
                throughput = self.num_samples / self.timer.split()
                top_1_accuracy = self.top_1_num_matched / self.num_samples
                top_k_accuracy = self.top_k_num_matched / self.num_samples
                if self.loss_key:
                    loss = outputs[self.loss_key].mean()
                    print(self.fmt.format(self.desc, epoch, step, loss, top_1_accuracy, 
                                          top_k_accuracy, throughput))
                    #summary.scalar('loss', loss, step)
                else:
                    print(self.fmt.format(self.desc, epoch, step, top_1_accuracy, top_k_accuracy,
                                          throughput))

                #summary.scalar('train_accuracy', accuracy, step)
                self._clear()
        return callback
    

