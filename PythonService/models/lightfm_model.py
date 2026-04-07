import numpy as np
import pandas as pd
from lightfm import LightFM
from lightfm.data import Dataset
from typing import List, Dict, Tuple
import joblib
import os
from utils.config import config

class LightFMRecommender:
    def __init__(self):
        self.model = None
        self.dataset = None
        self.item_features = None
        self.user_features = None
        
    def prepare_dataset(self, interactions: List[Tuple[str, str, float]],
                       user_features: Dict[str, List[str]] = None,
                       item_features: Dict[str, List[str]] = None):
        self.dataset = Dataset()

        users = list(set([interaction[0] for interaction in interactions]))
        items = list(set([interaction[1] for interaction in interactions]))

        self.dataset.fit(users=users, items=items)

        if user_features:
            all_user_features = set()
            for features in user_features.values():
                all_user_features.update(features)
            self.dataset.fit_partial(users=users, user_features=list(all_user_features))

        if item_features:
            all_item_features = set()
            for features in item_features.values():
                all_item_features.update(features)
            self.dataset.fit_partial(items=items, item_features=list(all_item_features))

        self.interactions, self.weights = self.dataset.build_interactions(
            [(interaction[0], interaction[1], interaction[2]) for interaction in interactions]
        )

        self.user_features_matrix = None
        if user_features:
            self.user_features_matrix = self.dataset.build_user_features(
                [(user, features) for user, features in user_features.items()]
            )

        self.item_features_matrix = None
        if item_features:
            self.item_features_matrix = self.dataset.build_item_features(
                [(item, features) for item, features in item_features.items()]
            )
    
    def train(self, epochs: int = None):
        if epochs is None:
            epochs = config.LIGHTFM_EPOCHS
            
        self.model = LightFM(loss='warp', no_components=config.LIGHTFM_COMPONENTS)
        self.model.fit(
            self.interactions,
            user_features=self.user_features_matrix,
            item_features=self.item_features_matrix,
            epochs=epochs,
            num_threads=4,
            verbose=True
        )
    
    def recommend(self, user_id: str, item_ids: List[str], num_recs: int = 10) -> List[Tuple[str, float]]:
        if self.model is None:
            raise ValueError("Модель не обучена. Сначала вызовите train()")

        user_internal_id = self.dataset.mapping()[0][user_id]

        item_internal_ids = [self.dataset.mapping()[2][item_id] for item_id in item_ids]

        scores = self.model.predict(
            user_ids=user_internal_id,
            item_ids=item_internal_ids,
            user_features=self.user_features_matrix,
            item_features=self.item_features_matrix,
            num_threads=4
        )

        recommendations = list(zip(item_ids, scores))
        recommendations.sort(key=lambda x: x[1], reverse=True)

        return recommendations[:num_recs]

    def save_model(self, path: str):
        if self.model:
            joblib.dump({
                'model': self.model,
                'dataset': self.dataset,
                'user_features': self.user_features_matrix,
                'item_features': self.item_features_matrix
            }, path)

    def load_model(self, path: str):
        if os.path.exists(path):
            data = joblib.load(path)
            self.model = data['model']
            self.dataset = data['dataset']
            self.user_features_matrix = data['user_features']
            self.item_features_matrix = data['item_features']