from app.core.strategies import IAStrategy, StrategyFastModel, StrategyCodeModel

class IAStrategyFactory:

    # Define a mapping of strategy types to their corresponding classes
    # Put here all the strategies you want to support
    _strategies = {
        'fast': StrategyFastModel,
        'code': StrategyCodeModel
    }
    @classmethod
    def obtain_strategy(cls, strategy_type: str) -> IAStrategy:
        """Factory method to obtain a strategy instance based on the provided type."""

        class_strategy = cls._strategies.get(strategy_type)

        # If the strategy type is not found, raise an exception
        if not class_strategy:
            available_strategies = list(cls._strategies.keys())
            raise ValueError(f"Strategy type '{strategy_type}' is not supported. Available strategies: {available_strategies}")
        
        # Return an instance of the strategy class
        return class_strategy()

