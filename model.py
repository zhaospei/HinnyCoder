import pandas as pd
import torch
from typing import Any, Dict, List, Optional, Tuple, Union
from torch import nn
from transformers import DefaultDataCollator
from transformers import Trainer


class DualObjectiveDataCollator(DefaultDataCollator):
    def __call__(self, features, return_tensors=None):
        features_df = pd.DataFrame(features)
        des_features = features_df.loc[:, ~features_df.columns.isin(['type_labels', 'type_input_ids', 'type_attention_mask'])].to_dict('records')
        type_features = features_df.loc[:, ~features_df.columns.isin(['labels', 'input_ids', 'attention_mask'])].rename(
            columns={'type_labels': 'labels', 'type_input_ids': 'input_ids', 'type_attention_mask': 'attention_mask'}).to_dict('records')

        des_features = super().__call__(des_features, return_tensors)
        type_features = super().__call__(type_features, return_tensors)

        return {
            'des': des_features,
            'type': type_features,
        }


class DualObjectiveTrainer(Trainer):
    def __init__(self, alpha, output_type, **kwargs):
        super().__init__(**kwargs)
        self.alpha = alpha
        self.output_type = output_type


    def compute_loss(self, model, inputs, return_outputs=False):
        des_outputs = model(**inputs['des'])
        type_outputs = model(**inputs['type'])
        
        loss = self.alpha * des_outputs.loss + (1. - self.alpha) * type_outputs.loss

        return (loss, {'des': des_outputs, 'type': type_outputs}) if return_outputs else loss


    def prediction_step(
        self,
        model: nn.Module,
        inputs: Dict[str, Union[torch.Tensor, Any]],
        prediction_loss_only: bool,
        ignore_keys: Optional[List[str]] = None
    ) -> Tuple[Optional[float], Optional[torch.Tensor], Optional[torch.Tensor]]:
        
        des_outputs = super().prediction_step(model, inputs['des'], prediction_loss_only=False, ignore_keys=ignore_keys)
        if self.output_rationale:
            type_outputs = super().prediction_step(model, inputs['type'], prediction_loss_only=False, ignore_keys=ignore_keys)
        else:
            type_outputs = des_outputs # placeholder only

        loss = self.alpha * des_outputs[0]  + (1 - self.alpha) * type_outputs[0]

        return (
            loss,
            [des_outputs[1], type_outputs[1]],
            [des_outputs[2], type_outputs[2]],
        )