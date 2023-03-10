from typing import Dict

import numpy as np


class Result:
    """
        Produce an object that stores the results for a fold
        Attributes:
            best_acc - float: the best accuracy of model
            best_epoch - integer: epoch number of the best accuracy
            precision - precision generated by classification report using test data
            recall - recall generated by classification report using test data
            f1_score - f1_score generated by classification report using test data
    """

    def __init__(self, classification_report=None):
        self.best_acc = 0
        self.best_epoch = 0
        self.precision = 0
        self.recall = 0
        self.f1_score = 0
        if classification_report is not None:
            self.set_values_from_classification_report(classification_report)

    def set_values_from_classification_report(self, classification_report: Dict[str, dict]) -> None:
        """
            Set the attributes of the class to values from a classification report

            :param classification_report: Dictionary summary of the precision, recall, F1 score for each class.
        """
        self.f1_score = classification_report["weighted avg"]["f1-score"]
        self.precision = classification_report["weighted avg"]["precision"]
        self.recall = classification_report["weighted avg"]["recall"]
        self.best_acc = classification_report["best_result"]["best_acc"]
        self.best_epoch = classification_report["best_result"]["best_epoch"]


class IterationResults:
    """
       Produce an object that stores all folds of results for an iteration
       Attributes:
           fold_results - array_like: array of fold result obejcts
   """

    def __init__(self):
        self.fold_results = []

    def add_result(self, result: Result) -> None:
        """
        Add a result of a fold to the array

        :param result: Results for a certain fold to be added to iteration
        """
        self.fold_results.append(result)

    def print_result(self) -> Dict[str, np.ndarray]:
        """
        Prints results of each fold and the average of all folds in iteration

        :return: Dictionary of average precision, recall and f1_score for all folds in an iteration
        """

        for i, result in enumerate(self.fold_results):
            print("Fold ", i + 1)
            print("Weighted Precision: {}  Weighted Recall: {}  Weighted F score: {}".format(
                result.precision,
                result.recall,
                result.f1_score))
            print(f'best_epoch:{result.best_epoch}, best_acc:{result.best_acc}')

        avg_precision = np.mean([result.precision for result in self.fold_results])
        avg_recall = np.mean([result.recall for result in self.fold_results])
        avg_f1_score = np.mean([result.f1_score for result in self.fold_results])

        print("#" * 20)
        print("Avg :")
        print("Weighted Precision: {:.3f}  Weighted Recall: {:.3f}  Weighted F score: {:.3f}".format(
            avg_precision, avg_recall, avg_f1_score))

        return {
            'precision': avg_precision,
            'recall': avg_recall,
            'f1_score': avg_f1_score
        }
