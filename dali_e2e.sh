rm -rf core.* 
rm -rf output/snapshots/*
#DATA_ROOT=/mnt/13_nfs/xuan/ImageNet/mxnet
DATA_ROOT=/ssd/ImageNet/mxnet
#DATA_ROOT=/dataset/imagenet-mxnet
  #python3 cnn_benchmark/of_cnn_train_val.py \
#gdb --args \
#nvprof -f -o resnet.nvvp \
  python3 cnn_e2e/dali_cnn_train_val.py \
    --data_train=$DATA_ROOT/train.rec \
    --data_train_idx=$DATA_ROOT/train.idx \
    --data_val=$DATA_ROOT/val.rec \
    --data_val_idx=$DATA_ROOT/val.idx \
    --num_nodes=2 \
    --node_ips='11.11.1.12,11.11.1.14' \
    --gpu_num_per_node=4 \
    --optimizer="momentum-cosine-decay" \
    --learning_rate=0.256 \
    --loss_print_every_n_iter=20 \
    --batch_size_per_device=32 \
    --val_batch_size_per_device=125 \
    --model="resnet50" 
    #--use_fp16 true \
    #--weight_l2=3.0517578125e-05 \
    #--num_examples=1024 \
    #--optimizer="momentum-decay" \
    #--data_dir="/mnt/13_nfs/xuan/ImageNet/ofrecord/train"
    #--data_dir="/mnt/dataset/xuan/ImageNet/ofrecord/train"
    #--warmup_iter_num=10000 \
