import pandas as pd
import torch
from typing import Any, Dict, List, Optional, Tuple, Union, Sequence

from torch import nn
import transformers
from transformers import DefaultDataCollator
from transformers import Trainer
from dataclasses import dataclass, field
IGNORE_INDEX = -100

@dataclass
class DataCollatorForDualObjectiveDataset(object):
    """Collate examples for dual objective fine-tuning."""
    tokenizer: transformers.PreTrainedTokenizer

    def __call__(self, instances: Sequence[Dict]) -> Dict[str, torch.Tensor]:
        func_input_ids, func_labels, class_input_ids, func_labels = tuple([instance[key] for instance in instances] for key in ("func_input_ids","func_labels","class_input_ids", "class_labels"))
        
        #func_input_preprocess
        func_input_ids = [torch.tensor(x) for x in func_input_ids]
        func_input_ids = torch.nn.utils.rnn.pad_sequence(
            func_input_ids, batch_first=True, padding_value=self.tokenizer.pad_token_id
        )
        func_labels = [torch.tensor(x) for x in func_labels]
        func_labels = torch.nn.utils.rnn.pad_sequence(func_labels, batch_first=True, padding_value=IGNORE_INDEX)
        
        #class_input_preprocess
        class_input_ids = [torch.tensor(x) for x in class_input_ids]
        class_input_ids = torch.nn.utils.rnn.pad_sequence(
            class_input_ids, batch_first=True, padding_value=self.tokenizer.pad_token_id
        )
        class_labels = [torch.tensor(x) for x in class_labels]
        class_labels = torch.nn.utils.rnn.pad_sequence(class_labels, batch_first=True, padding_value=IGNORE_INDEX)
        return {
            'func':  dict(
                input_ids=func_input_ids, 
                labels=func_labels, 
                attention_mask=func_input_ids.ne(self.tokenizer.pad_token_id),
            ),
            'class': dict(
                input_ids=class_input_ids, 
                labels=class_labels, 
                attention_mask=class_input_ids.ne(self.tokenizer.pad_token_id),
            ),
        }


class DualObjectiveTrainer(Trainer):
    def __init__(self, alpha, output_function, **kwargs):
        super().__init__(**kwargs)
        self.alpha = alpha
        self.output_function = output_function


    def compute_loss(self, model, inputs, return_outputs=False):
        class_outputs = model(**inputs['class'])
        func_outputs = model(**inputs['func'])
        
        loss = self.alpha * class_outputs.loss + (1. - self.alpha) * func_outputs.loss

        return (loss, {'class': class_outputs, 'func': func_outputs}) if return_outputs else loss


    def prediction_step(
        self,
        model: nn.Module,
        inputs: Dict[str, Union[torch.Tensor, Any]],
        prediction_loss_only: bool,
        ignore_keys: Optional[List[str]] = None
    ) -> Tuple[Optional[float], Optional[torch.Tensor], Optional[torch.Tensor]]:
        
        class_outputs = super().prediction_step(model, inputs['class'], prediction_loss_only=False, ignore_keys=ignore_keys)
        if self.output_function:
            func_outputs = super().prediction_step(model, inputs['func'], prediction_loss_only=False, ignore_keys=ignore_keys)
        else:
            func_outputs = class_outputs # placeholder only

        loss = self.alpha * class_outputs[0]  + (1 - self.alpha) * class_outputs[0]

        return (
            loss,
            [class_outputs[1], func_outputs[1]],
            [class_outputs[2], func_outputs[2]],
        )