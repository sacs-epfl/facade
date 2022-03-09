from torch import nn


class Model(nn.Module):
    """
    This class wraps the torch model
    More fields can be added here

    """

    def __init__(self):
        """
        Constructor

        """
        super().__init__()
        self.accumulated_gradients = []
        self._param_count_ot = None
        self._param_count_total = None
        self.accumulated_frequency = None
        self.prev_model_params = None
        self.prev = None

    def count_params(self, only_trainable=False):
        """
        Counts the total number of params

        Parameters
        ----------
        only_trainable : bool
            Counts only parameters with gradients when True

        Returns
        -------
        int
            Total number of parameters

        """
        if only_trainable:
            if not self._param_count_ot:
                self._param_count_ot = sum(
                    p.numel() for p in self.parameters() if p.requires_grad
                )
            return self._param_count_ot
        else:
            if not self._param_count_total:
                self._param_count_total = sum(p.numel() for p in self.parameters())
            return self._param_count_total
