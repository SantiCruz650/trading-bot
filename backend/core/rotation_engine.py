import logging

logger = logging.getLogger(__name__)

class RotationEngine:
    def __init__(self, config=None):
        self.config = config or {}
        self.min_shs_to_trade = self.config.get("min_shs_to_trade", 40)

    def calculate_shs(self, metrics):
        """
        Symbol Health Score (SHS) calculation (0-100).
        metrics: {accuracy, trend_strength, win_rate, volatility_adj}
        """
        w_accuracy = 0.4
        w_trend = 0.2
        w_win_rate = 0.3
        w_vol = 0.1

        score = (
            metrics.get("accuracy", 0) * 100 * w_accuracy +
            metrics.get("trend_strength", 0) * 100 * w_trend +
            metrics.get("win_rate", 0) * 100 * w_win_rate +
            (1 - metrics.get("volatility", 0)) * 100 * w_vol
        )
        return max(0, min(100, score))

    def reallocate_capital(self, symbols_data, total_available_capital):
        """
        Reallocates capital based on SHS across multiple symbols.
        symbols_data: {ticker: {metrics}}
        Returns: {ticker: allocated_amount}
        """
        scores = {}
        total_score = 0
        
        for ticker, data in symbols_data.items():
            shs = self.calculate_shs(data.get("metrics", {}))
            if shs >= self.min_shs_to_trade:
                scores[ticker] = shs
                total_score += shs
            else:
                scores[ticker] = 0
                logger.info(f"Symbol {ticker} blocked by SHS: {shs:.2f}")

        allocations = {}
        if total_score > 0:
            for ticker, score in scores.items():
                allocations[ticker] = (score / total_score) * total_available_capital
        
        return allocations
