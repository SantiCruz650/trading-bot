class RiskGovernor:
    """
    Global Risk Governance.
    Monitors portfolio-wide risk levels.
    """
    def __init__(self, config):
        self.config = config
        # Initializing a basic risk manager inside to satisfy StrategyEngine calls
        from app.services.risk_manager import RiskManager
        self.risk_manager = RiskManager(bankroll=1000.0)

    def evaluate_risk(self, portfolio_stats):
        """Mock evaluation: Returns True (SAFE) for now."""
        return True

    def evaluate_global_risk(self, total_equity, portfolio_ath):
        """Mock evaluation: Returns a safe state for now."""
        return {"status": "SAFE", "total_equity": total_equity, "ath": portfolio_ath}

    def can_execute_intent(self, side, symbol_metrics):
        """Mock validation: Returns True (ALLOWED) for now."""
        return True, "Global risk within limits"
