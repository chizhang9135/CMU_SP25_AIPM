import yaml
from typing import Tuple

class MetricsEvaluator:
    def __init__(self, ground_truth_path: str, output_path: str):
        self.ground_truth = self.load_yaml(ground_truth_path)
        self.output = self.load_yaml(output_path)

    def load_yaml(self, path: str):
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def extract_features(self, entry: list) -> dict:
        """
        Extract features as a dictionary: {name: type}
        from the content string in the YAML list.
        """
        for item in entry:
            if item['role'] == 'system':
                content = item['content']
                break
        else:
            return {}

        features = {}
        for line in content.splitlines():
            line = line.strip()
            if line.startswith('"') and '":' in line:
                try:
                    name_type = line.split('"')
                    name = name_type[1]
                    rest = name_type[2]
                    typ = rest.strip().split(',')[0]
                    features[name] = typ
                except Exception:
                    continue
        return features

    def accuracy(self, dataset_key: str) -> Tuple[str, float]:
        gt_features = self.extract_features(self.ground_truth[dataset_key])
        out_features = self.extract_features(self.output[dataset_key])

        total = len(gt_features)
        correct = 0
        messages = []

        for key, typ in gt_features.items():
            if key in out_features and out_features[key] == typ:
                correct += 1
            elif key in out_features:
                messages.append(f"Wrong type for feature '{key}': expected '{typ}', got '{out_features[key]}'")
            else:
                messages.append(f"Missing feature '{key}'")

        acc = correct / total if total else 0

        if not messages:
            result_msg = "All features match."
        else:
            result_msg = "\n".join(messages)

        return result_msg, acc

    def coverage(self, dataset_key: str) -> Tuple[str, float]:
        gt_features = self.extract_features(self.ground_truth[dataset_key])
        out_features = self.extract_features(self.output[dataset_key])

        total = len(gt_features)
        coverage = 0
        missing = []

        for key in gt_features:
            if key in out_features:
                coverage += 1
            else:
                missing.append(f"Missing description for feature '{key}'")

        cov = coverage / total if total else 0

        if not missing:
            result_msg = "All features are described."
        else:
            result_msg = "\n".join(missing)

        return result_msg, cov

    def latency(self):
        pass

    def memory(self):
        pass

    def token(self):
        pass

    @staticmethod
    def help():
        print("""
MetricsEvaluator - Evaluate structured YAML outputs

Constructor:
- MetricsEvaluator(ground_truth_path: str, output_path: str)

Methods:
- accuracy(dataset_key: str) -> str, float
    Compare feature name and type accuracy.

- coverage(dataset_key: str) -> str, float
    Return percentage of features with names/types present in output, and list any missing descriptions.

- latency(), memory(), token(): Placeholders for future metrics.

Expected YAML format:
Each file is a dictionary with dataset name as key and a list of messages (with 'role' and 'content') as value.

Usage:
>>> evaluator = MetricsEvaluator('ground_truth.yaml', 'model_output.yaml')
>>> msg, acc = evaluator.accuracy('HeartDisease')
>>> cov_msg, cov = evaluator.coverage('HeartDisease')
>>> print(msg)
>>> print(cov_msg)
>>> print(f"Accuracy: {acc:.2%}, Coverage: {cov:.2%}")
        """)
