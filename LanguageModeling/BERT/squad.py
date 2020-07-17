import oneflow as flow
import bert as bert_util
import oneflow.core.operator.op_conf_pb2 as op_conf_util

def _ComputeLoss(logits, positions, seq_length):
  logits = flow.reshape(logits, [-1, seq_length])
  probs = flow.nn.softmax(logits)
  pre_example_loss = flow.nn.sparse_cross_entropy(labels=positions, prediction=probs)
  return pre_example_loss

def SQuADEval(
    unique_ids_blob, 
    input_ids_blob,
    input_mask_blob,
    token_type_ids_blob,
    vocab_size,
    seq_length=512,
    hidden_size=768,
    num_hidden_layers=12,
    num_attention_heads=12,
    intermediate_size=3072,
    hidden_act="gelu",
    hidden_dropout_prob=0.1,
    attention_probs_dropout_prob=0.1,
    max_position_embeddings=512,
    type_vocab_size=16,
    max_predictions_per_seq=20,
    initializer_range=0.02,
    ):

    backbone = bert_util.BertBackbone(
        input_ids_blob=input_ids_blob,
        input_mask_blob=input_mask_blob,
        token_type_ids_blob=token_type_ids_blob,
        vocab_size=vocab_size,
        seq_length=seq_length,
        hidden_size=hidden_size,
        num_hidden_layers=num_hidden_layers,
        num_attention_heads=num_attention_heads,
        intermediate_size=intermediate_size,
        hidden_act=hidden_act,
        hidden_dropout_prob=hidden_dropout_prob,
        attention_probs_dropout_prob=attention_probs_dropout_prob,
        max_position_embeddings=max_position_embeddings,
        type_vocab_size=type_vocab_size,
        initializer_range=initializer_range,
    )

    with flow.name_scope("cls-squad"):
        final_hidden = backbone.sequence_output()
        final_hidden_matrix = flow.reshape(final_hidden, [-1, hidden_size])
        logits = bert_util._FullyConnected(
                    final_hidden_matrix,
                    hidden_size,
                    units=2,
                    weight_initializer=bert_util.CreateInitializer(initializer_range),
                    name='output')
        logits = flow.reshape(logits, [-1, seq_length, 2])

        start_logits = flow.slice(logits, [None, None, 0], [None, None, 1])
        end_logits = flow.slice(logits, [None, None, 1], [None, None, 1])

    return unique_ids_blob, start_logits, end_logits


def SQuADTrain(
    input_ids_blob,
    input_mask_blob,
    token_type_ids_blob,
    start_positions_blob,
    end_positions_blob,
    vocab_size,
    seq_length=512,
    hidden_size=768,
    num_hidden_layers=12,
    num_attention_heads=12,
    intermediate_size=3072,
    hidden_act="gelu",
    hidden_dropout_prob=0.1,
    attention_probs_dropout_prob=0.1,
    max_position_embeddings=512,
    type_vocab_size=16,
    max_predictions_per_seq=20,
    initializer_range=0.02,
):
    backbone = bert_util.BertBackbone(
        input_ids_blob=input_ids_blob,
        input_mask_blob=input_mask_blob,
        token_type_ids_blob=token_type_ids_blob,
        vocab_size=vocab_size,
        seq_length=seq_length,
        hidden_size=hidden_size,
        num_hidden_layers=num_hidden_layers,
        num_attention_heads=num_attention_heads,
        intermediate_size=intermediate_size,
        hidden_act=hidden_act,
        hidden_dropout_prob=hidden_dropout_prob,
        attention_probs_dropout_prob=attention_probs_dropout_prob,
        max_position_embeddings=max_position_embeddings,
        type_vocab_size=type_vocab_size,
        initializer_range=initializer_range,
    )
    with flow.name_scope("cls-squad"):
        final_hidden = backbone.sequence_output()
        final_hidden_matrix = flow.reshape(final_hidden, [-1, hidden_size])
        logits = bert_util._FullyConnected(
                    final_hidden_matrix,
                    hidden_size,
                    units=2,
                    weight_initializer=bert_util.CreateInitializer(initializer_range),
                    name='output')
        logits = flow.reshape(logits, [-1, seq_length, 2])

        start_logits = flow.slice(logits, [None, None, 0], [None, None, 1])
        end_logits = flow.slice(logits, [None, None, 1], [None, None, 1])

        start_loss = _ComputeLoss(start_logits, start_positions_blob, seq_length)
        end_loss = _ComputeLoss(end_logits, end_positions_blob, seq_length)

        total_loss = 0.5*(start_loss + end_loss)

    return total_loss