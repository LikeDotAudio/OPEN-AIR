# workers/Splinker/handlers/base_handler.py

class BaseHandler:
    def __init__(self, params):
        self.params = params

    def execute(self, value, splink=None, state=None, direction="FORWARD"):
        """
        Executes the handler logic.
        
        Args:
            value: The incoming value from the source.
            splink (dict): The full splink configuration object.
            state (dict): A mutable state dictionary that persists for the lifetime of the pipeline instance.
            direction (str): "FORWARD" (Source -> Dest) or "REVERSE" (Dest -> Source).

        Returns:
            The modified value, or None to stop the pipeline.
        """
        raise NotImplementedError
