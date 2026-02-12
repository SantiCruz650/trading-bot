from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.models.models import Strategy, StrategyExecution, PaperTrade
from datetime import datetime, timedelta
import json
import httpx

class StrategyEngine:
    def __init__(self):
        # ETAPA 2A - Risk Manager
        from app.services.risk_manager import RiskManager
        self.risk_manager = RiskManager(bankroll=1000.0)  # Will be updated dynamically
        
        # ETAPA 2B Engines
        from app.core.ar_dca_engine import ARDCAEngine
        from app.core.rotation_engine import RotationEngine
        from app.core.risk_governor import RiskGovernor
        import yaml
        
        config_path = Path(__file__).resolve().parent.parent.parent / "etapa2b.yaml"
        # Fallback for different deployment structures
        if not config_path.exists():
             config_path = Path(__file__).resolve().parent.parent / "etapa2b.yaml"
             
        with open(config_path, 'r') as f:
            self.config_2b = yaml.safe_load(f)
            
        self.ar_dca_engine = ARDCAEngine(self.config_2b.get("ar_dca", {}))
        self.rotation_engine = RotationEngine(self.config_2b.get("rotation", {}))
        self.risk_governor = RiskGovernor(self.config_2b.get("risk_governor", {}))
        print("🤖 Strategy Engine Initialized (Persistent State)")

    def evaluate_strategies(self, ticker: str, current_price: float, db: Session):
        """Check all active strategies for this ticker and execute if needed."""
        # 0. Check Kill Switch
        if self.risk_governor.risk_manager.kill_switch_active:
            print(f"🛑 KILL SWITCH ACTIVE: Strategy evaluation HALTED for {ticker}")
            return
            
        strategies = db.query(Strategy).filter(
            Strategy.ticker == ticker, 
            Strategy.status == "ACTIVE"
        ).all()
        
        if strategies:
            print(f"🧠 Evaluating {len(strategies)} active strategies for {ticker} @ ${current_price:,.2f}")
        
        results = []
        for strategy in strategies:
            if strategy.type == "GRID":
                res = self._evaluate_grid(strategy, current_price, db)
            elif strategy.type == "DCA":
                res = self._evaluate_dca(strategy, current_price, db)
            
            if res:
                results.append(res)
        return results

    def _evaluate_dca(self, strategy, current_price, db):
        """
        DCA Logic: 
        1. Sell if price >= avg_buy_price + 1.5% (Trailing Take Profit)
        2. Buy if enough time has passed AND balance > 100 USDT
        3. Cooldown after sale: Wait 3 cycles
        4. Drawdown Guard: Pause if >4% drop in 10 mins
        """
        params = strategy.params or {}
        params["total_cycles"] = params.get("total_cycles", 0) + 1
        from app.core.config import settings
        from app.services.exchange_service import get_exchange
        exchange = get_exchange(local_simulation=settings.OBSERVATION_ONLY)
        
        amount_to_buy = params.get("amount", settings.BASE_TRADE_AMOUNT)
        # 1. Get current position stats
        avg_price, total_eth, dca_levels = self._get_position_stats(strategy, db)
        current_balance = exchange.get_balance()
        
        # 1.1 Calculate Dynamic Position Size
        amount_to_buy, params = self._calculate_dynamic_size(strategy, current_price, current_balance, total_eth)
        
        # 1.2 ETAPA 2A - Update Risk Manager State
        total_position_value = total_eth * current_price
        self.risk_manager.update_equity(current_balance, total_position_value)
        self.risk_manager.update_gec_state()
        
        interval_hours = params.get("interval_hours", 24)
        
        # 2. ML Insight (Passive & Active Filter)
        ml_data = self._log_ml_insight(strategy, current_price)
        ml_signal = ml_data.get("signal", "NEUTRAL")
        ml_regime = ml_data.get("regime", "UNKNOWN")
        ml_strictness = ml_data.get("strictness", "NORMAL")
        ml_confidence = ml_data.get("confidence", 0.5)
        
        # 2.1 ETAPA 2B Metrics Analysis
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{settings.ML_SERVICE_URL}/metrics/{strategy.ticker}")
                if resp.status_code == 200:
                    ml_metrics = resp.json()
                else:
                    ml_metrics = {}
        except:
            ml_metrics = {}
            
        # 2.2 Global Risk Governance
        portfolio_stats = self._get_global_portfolio_stats(db)
        global_state = self.risk_governor.evaluate_global_risk(
            total_equity=portfolio_stats["total_equity"],
            portfolio_ath=portfolio_stats["portfolio_ath"]
        )
        
        # 2.3 Calculate Symbol Health Score (SHS) for Rotation
        shs = self.rotation_engine.calculate_shs(ml_metrics)
        symbol_risk_metrics = {"shs": shs}
        
        # Check execution intent with Risk Governor
        can_exec, risk_msg = self.risk_governor.can_execute_intent("BUY", symbol_risk_metrics)
        if not can_exec:
            print(f"🛡️ Risk Governor: BUY blocked - {risk_msg}")
            can_buy = False # Will be used below
        
        # 2.4 Evaluate ML Performance
        self._evaluate_ml_performance(strategy, current_price, db)
        
        # 3. Drawdown Guard & Market Regime Data
        price_history = params.get("price_history", [])
        now = datetime.utcnow()
        # Keep last 200 points for EMA calculation (~50 mins at 15s)
        price_history = price_history[-199:]
        price_history.append({'ts': now.isoformat(), 'price': current_price})
        params['price_history'] = price_history
        
        paused_until = params.get("paused_until")
        if paused_until and now < datetime.fromisoformat(paused_until):
            strategy.params = params
            flag_modified(strategy, "params")
            self.db.commit()
            return None

        # 3.1 Market Regime Detection
        regime = ml_regime if ml_regime != "UNKNOWN" else self._detect_market_regime(params)
        print(f"🌐 Market Regime: {regime} (Strictness: {ml_strictness})")
        
        # 3.2 ETAPA 2A - Check Freeze Conditions
        self.risk_manager.check_freeze_conditions(regime)
        
        if len(price_history) > 1:
            # For drawdown, we still only look at the last 10 minutes
            ten_mins_ago = now - timedelta(minutes=10)
            recent_prices = [p for p in price_history if datetime.fromisoformat(p['ts']) > ten_mins_ago]
            if recent_prices:
                oldest_price = recent_prices[0]['price']
                drop_pct = (current_price - oldest_price) / oldest_price
                if drop_pct <= -0.04:
                    params['paused_until'] = (now + timedelta(minutes=30)).isoformat()
                    print(f"🚨 Drawdown detected ({drop_pct*100:.1f}%). Buying paused for 30m.")
                    strategy.params = params
                    flag_modified(strategy, "params")
                    db.commit()
                    return None

        # 4. Check Sell Condition (Trailing Take Profit)
        if total_eth > 0 and avg_price > 0:
            profit_pct = (current_price - avg_price) / avg_price
            
            ttp_active = params.get("ttp_active", False)
            highest_price = params.get("highest_price", 0.0)
            
            # ETAPA 2A - Adjust TTP target if Hard Cap active
            ttp_threshold = 0.015  # Default 1.5%
            if self.risk_manager.gec_state == "HARD_CAP":
                ttp_threshold = 0.001  # Break-even + 0.1% in Hard Cap mode
                print(f"🚫 Hard Cap Active: TTP adjusted to break-even + 0.1%")
            
            if profit_pct >= ttp_threshold or ttp_active:
                if not ttp_active:
                    params["ttp_active"] = True
                    params["highest_price"] = current_price
                    print(f"🎯 TTP Armed for {strategy.ticker} at ${current_price:,.2f}")
                else:
                    if current_price > highest_price:
                        params["highest_price"] = current_price
                    
                    drop_from_peak = (params["highest_price"] - current_price) / params["highest_price"]
                    if drop_from_peak >= 0.0075:
                        eth_to_sell = total_eth * 0.20
                        if eth_to_sell * current_price > 1.0:
                            # Reset TTP
                            params["ttp_active"] = False
                            params["highest_price"] = 0.0
                            # Set Cooldown
                            params["cooldown_cycles"] = 3
                            strategy.params = params
                            flag_modified(strategy, "params")
                            # We commit before trade to ensure params are saved if trade fails
                            db.commit()
                            
                            if settings.OBSERVATION_ONLY:
                                print(f"🔭 Observation Mode: SELL signal for {strategy.ticker} at ${current_price:,.2f} (No trade executed)")
                                return None
                                
                            result = self._execute_trade(strategy, "SELL", eth_to_sell * current_price, current_price, db, avg_buy_price)
                            # Record cycle outcome
                            profitable = current_price > avg_price
                            self.risk_manager.record_cycle_outcome(profitable=profitable)
                            return result

        # 5. Check Buy Condition (Intelligent DCA + Cooldown)
        cooldown = params.get("cooldown_cycles", 0)
        if cooldown > 0:
            print(f"⏸ Cooldown active ({4-cooldown}/3)")
            params["cooldown_cycles"] -= 1
            strategy.params = params
            flag_modified(strategy, "params")
            self.db.commit()
            return None

        can_buy = True
        
        # ETAPA 2A - Check Risk Manager approval for new position
        risk_can_open, risk_reason = self.risk_manager.can_open_position("BUY")
        if not risk_can_open:
            print(f"🛡️ ETAPA 2A: BUY blocked - {risk_reason}")
            # If Hard Cap, cancel pending orders (simulated)
            if self.risk_manager.gec_state == "HARD_CAP":
                print(f"🚫 Hard Cap: Canceling pending BUY orders (simulated)")
            strategy.params = params
            flag_modified(strategy, "params")
            self.db.commit()
            return None
        
        # Dynamic Observation Mode: Force observation if balance is low
        if current_balance < 100:
            if not settings.OBSERVATION_ONLY:
                print(f"⚠️ Low Balance ({current_balance:.2f} < 100). Forced OBSERVATION_ONLY mode.")
            can_buy = False
        elif current_balance > 150:
            can_buy = True
            
        # ML Filter: Defensive Rules (Stage 1.1)
        ml_confidence = ml_data.get("confidence", 0.5)
        block_reason = None

        if ml_signal == "SELL":
            block_reason = f"SELL signal (Regime: {regime})"
            can_buy = False
        elif regime == "HIGH_VOLATILITY":
            block_reason = "HIGH_VOLATILITY hard stop"
            can_buy = False
        elif regime == "TREND_DOWN" and ml_confidence < 0.55:
            block_reason = f"TREND_DOWN with low confidence ({ml_confidence:.2f} < 0.55)"
            can_buy = False
        elif regime == "RANGE" and dca_levels > 3800 and ml_confidence < 0.50:
            block_reason = f"RANGE with high DCA ({dca_levels} > 3800) and low confidence ({ml_confidence:.2f} < 0.50)"
            can_buy = False
        elif ml_signal == "HOLD" and ml_data.get("original_signal") == "BUY":
            block_reason = f"Regime Strictness ({ml_strictness})"
            can_buy = False

        if block_reason:
            print(f"🧠 ML Filter: BUY blocked - {block_reason}")

        if can_buy:
            # Get last BUY execution
            last_buy = db.query(StrategyExecution).filter(
                StrategyExecution.strategy_id == strategy.id,
                StrategyExecution.order_type == "BUY"
            ).order_by(StrategyExecution.timestamp.desc()).first()
            
            should_buy = False
            if not last_buy:
                should_buy = True
            else:
                time_since = datetime.utcnow() - last_buy.timestamp
                # ETAPA 2B - Enforce min interval from config
                min_interval_sec = self.config_2b.get("ar_dca", {}).get("min_dca_interval_seconds", 0)
                
                if time_since >= timedelta(hours=interval_hours) and time_since >= timedelta(seconds=min_interval_sec):
                    should_buy = True
            
            if should_buy:
                # ETAPA 2B - Apply AR-DCA Adaptive Multiplier
                volatility = ml_metrics.get("volatility", 0.02)
                ar_multiplier = self.ar_dca_engine.calculate_order_multiplier(
                    volatility=volatility,
                    trend=regime,
                    ml_confidence=ml_confidence,
                    current_drawdown=portfolio_stats["drawdown"]
                )
                amount_to_buy *= ar_multiplier
                
                # Apply GEC Adjustments
                gec_adjustments = self.risk_manager.get_gec_adjustments()
                amount_to_buy *= gec_adjustments["order_size_multiplier"]
                interval_hours *= gec_adjustments["dca_step_multiplier"]
                
                # Regime Adjustments
                if regime == "TREND_DOWN":
                    amount_to_buy *= 0.5
                    print(f"📉 Trend Down: Reducing buy amount to {amount_to_buy:.2f} USDT")
                elif regime == "HIGH_VOLATILITY":
                    params["cooldown_cycles"] = 6
                    print(f"⚡ High Volatility: Activating extended cooldown (6 cycles)")
                
                strategy.params = params
                flag_modified(strategy, "params")
                
                if settings.OBSERVATION_ONLY or current_balance < 100:
                    # Anti-spam: Only log once per hour per ticker in observation mode
                    last_log = params.get("last_observation_buy_log")
                    now_iso = datetime.utcnow().isoformat()
                    if not last_log or (datetime.utcnow() - datetime.fromisoformat(last_log)).total_seconds() > 3600:
                        print(f"🔭 Observation Mode: BUY signal for {strategy.ticker} at ${current_price:,.2f} (No trade executed)")
                        params["last_observation_buy_log"] = now_iso
                        strategy.params = params
                        flag_modified(strategy, "params")
                        db.commit()
                    return None
                
                # Log for ML Evaluation
                from core.ml_evaluator import MLEvaluator
                evaluator = MLEvaluator()
                # Calculate current drawdown for logging
                ath = params.get("equity_ath", current_balance + (total_eth * current_price))
                current_equity = current_balance + (total_eth * current_price)
                drawdown = (ath - current_equity) / ath if ath > 0 else 0
                
                evaluator.log_event(
                    ticker=strategy.ticker,
                    price=current_price,
                    ml_signal=ml_signal,
                    original_signal="BUY", # Representing Algorithm's intent
                    regime=regime,
                    action_taken="EXECUTED",
                    drawdown=drawdown,
                    dca_levels=dca_levels
                )
                    
                return self._execute_trade(strategy, "BUY", amount_to_buy, current_price, db)
        
        # If we reached here, either can_buy was False or should_buy was False
        # If it was blocked by ML (block_reason exists) and algo wanted to buy (balance >= 100)
        if block_reason and current_balance >= 100:
            from core.ml_evaluator import MLEvaluator
            evaluator = MLEvaluator()
            # Calculate current drawdown for logging
            ath = params.get("equity_ath", current_balance + (total_eth * current_price))
            current_equity = current_balance + (total_eth * current_price)
            drawdown = (ath - current_equity) / ath if ath > 0 else 0
            
            evaluator.log_event(
                ticker=strategy.ticker,
                price=current_price,
                ml_signal=ml_signal,
                original_signal="BUY", # Representing Algorithm's intent
                regime=regime,
                action_taken="BLOCKED_BY_ML",
                drawdown=drawdown,
                dca_levels=dca_levels
            )
        
        strategy.params = params
        flag_modified(strategy, "params")
        db.commit()
        return None

    def _calculate_dynamic_size(self, strategy, current_price, current_balance, total_eth):
        params = strategy.params or {}
        
        # 1. Calculate Current Equity
        current_equity = current_balance + (total_eth * current_price)
        
        # 2. Track Equity ATH
        if "equity_ath" not in params:
            params["equity_ath"] = current_equity
        elif current_equity > params["equity_ath"]:
            params["equity_ath"] = current_equity
        
        ath = params["equity_ath"]
            
        # 3. Calculate Drawdown
        drawdown = (ath - current_equity) / ath if ath > 0 else 0
        
        # 4. Calculate Volatility (from last 10 mins)
        price_history = [p['price'] for p in params.get("price_history", [])]
        volatility = 0.0
        if len(price_history) > 5:
            import statistics
            mean_price = statistics.mean(price_history)
            stdev_price = statistics.stdev(price_history)
            volatility = stdev_price / mean_price if mean_price > 0 else 0
            
        # 5. Adjustment Logic
        base_size = 2.0
        size = base_size
        reason = "Base size"
        
        if drawdown > 0.02:
            size = 1.0
            reason = f"Drawdown protection ({drawdown*100:.1f}%)"
        elif volatility > 0.005:
            size = 1.0
            reason = f"High volatility ({volatility*100:.2f}%)"
        elif current_equity >= ath * 0.999 and volatility < 0.001:
            size = 3.0
            reason = "Equity ATH + Low volatility"
            
        # Constraints
        size = max(1.0, min(5.0, size))
        
        if size != base_size:
            print(f"⚖️ Position Size Adjusted: {size:.2f} USDT (Reason: {reason})")
            
        return size, params

    def _detect_market_regime(self, params):
        price_history = [p['price'] for p in params.get("price_history", [])]
        if len(price_history) < 50:
            return "INITIALIZING"
            
        # Calculate EMAs
        def calculate_ema(prices, period):
            ema = prices[0]
            multiplier = 2 / (period + 1)
            for price in prices[1:]:
                ema = (price - ema) * multiplier + ema
            return ema
            
        ema50 = calculate_ema(price_history, 50)
        ema200 = calculate_ema(price_history, 200) if len(price_history) >= 200 else calculate_ema(price_history, len(price_history))
        current_price = price_history[-1]
        
        # Calculate Volatility (ATR-like range)
        recent_ranges = []
        for i in range(1, min(20, len(price_history))):
            recent_ranges.append(abs(price_history[-i] - price_history[-i-1]))
        
        avg_range = sum(recent_ranges) / len(recent_ranges) if recent_ranges else 0
        current_range = abs(price_history[-1] - price_history[-2]) if len(price_history) > 1 else 0
        
        if current_range > avg_range * 3.0:
            return "HIGH_VOLATILITY"
        
        if current_price > ema50 and ema50 > ema200:
            return "TREND_UP"
        elif current_price < ema50 and ema50 < ema200:
            return "TREND_DOWN"
        else:
            return "RANGE"

    def _get_position_stats(self, strategy, db):
        """Calculate average buy price, total ETH held, and DCA levels for this strategy."""
        executions = db.query(StrategyExecution).filter(
            StrategyExecution.strategy_id == strategy.id
        ).all()
        
        total_eth = 0.0
        total_cost = 0.0
        dca_levels = 0
        
        for ex in executions:
            eth_amount = ex.amount / ex.price
            if ex.order_type == "BUY":
                total_eth += eth_amount
                total_cost += ex.amount
                dca_levels += 1
            else:
                # For sells, we reduce the position proportionally
                if total_eth > 0:
                    avg_price = total_cost / total_eth
                    total_eth -= eth_amount
                    total_cost -= (avg_price * eth_amount)
                    # If position is closed, reset levels
                    if total_eth <= 1e-8:
                        dca_levels = 0
        
        if total_eth <= 0:
            return 0.0, 0.0, 0
            
        avg_price = total_cost / total_eth
        return avg_price, total_eth, dca_levels

    def _log_ml_insight(self, strategy, current_price, db): # Added db although not used yet to keep consistent
        """Fetch and log ML signal and record correlation."""
        ticker = strategy.ticker
        data = {"signal": "NEUTRAL", "regime": "UNKNOWN", "strictness": "NORMAL"}
        try:
            from app.core.config import settings
            ml_url = f"{settings.ML_SERVICE_URL}/predict/{ticker}"
            # We use a short timeout to not block the loop
            with httpx.Client(timeout=2.0) as client:
                response = client.get(ml_url)
                if response.status_code == 200:
                    data = response.json()
                    ml_signal = data.get("signal", "NEUTRAL")
                    # Use actual confidence if available, otherwise mock it
                    prob = data.get("confidence", 0.5 + (0.1 if ml_signal == "BUY" else -0.1 if ml_signal == "SELL" else 0))
                    data["confidence"] = prob
                    # Only log if not already logged recently to avoid spam, or if signal changed
                    # For now, we log every time as requested in "Logging y Visibilidad"
                    # print(f"🧠 ML Insight {ticker}: {ml_signal} ({prob:.2f})")
                    
                    # Record for correlation
                    log_path = Path(__file__).resolve().parent.parent.parent / "ml_correlation.log"
                    with open(log_path, "a") as f:
                        f.write(f"{datetime.utcnow().isoformat()} | {ticker} | {ml_signal} | {current_price:.2f}\n")
                        
                    # Store for evaluation
                    params = strategy.params or {}
                    pending = params.get("pending_ml_evaluations", [])
                    pending.append({
                        "signal": ml_signal,
                        "entry_price": current_price,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    params["pending_ml_evaluations"] = pending
                    strategy.params = params
                    flag_modified(strategy, "params")
                    db.commit()
        except Exception:
            # Silent fail for ML insight to maintain stability
            pass
        return data

    def _evaluate_ml_performance(self, strategy, current_price, db):
        """Evaluate pending ML signals after 1 hour."""
        params = strategy.params or {}
        pending = params.get("pending_ml_evaluations", [])
        if not pending:
            return
            
        now = datetime.utcnow()
        eval_log_path = Path(__file__).resolve().parent.parent.parent / "ml_evaluation.log"
        
        new_pending = []
        metrics = params.get("ml_metrics", {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "total": 0})
        
        for p in pending:
            ts = datetime.fromisoformat(p["timestamp"])
            if (now - ts).total_seconds() >= 3600: # 1 hour
                signal = p["signal"]
                entry_price = p["entry_price"]
                metrics["total"] += 1
                
                result = "NEUTRAL"
                if signal == "BUY":
                    if current_price > entry_price:
                        metrics["tp"] += 1
                        result = "SUCCESS"
                    else:
                        metrics["fp"] += 1
                        result = "FAILURE"
                elif signal == "SELL":
                    if current_price < entry_price:
                        metrics["tp"] += 1 # We count correct SELL as TP for simplicity in this context
                        result = "SUCCESS"
                    else:
                        metrics["fp"] += 1
                        result = "FAILURE"
                
                # Log individual evaluation
                with open(eval_log_path, "a") as f:
                    f.write(f"{now.isoformat()} | {strategy.ticker} | Signal: {signal} | Entry: {entry_price:.2f} | Exit: {current_price:.2f} | Result: {result}\n")
            else:
                new_pending.append(p)
        
        if len(new_pending) != len(pending):
            # Calculate cumulative metrics
            tp = metrics["tp"]
            fp = metrics["fp"]
            total = metrics["total"]
            
            accuracy = tp / total if total > 0 else 0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            
            # Log summary
            with open(eval_log_path, "a") as f:
                f.write(f"📊 ML SUMMARY | Ticker: {strategy.ticker} | Accuracy: {accuracy:.2f} | Precision: {precision:.2f} | Total Evaluated: {total}\n")
            
            params["pending_ml_evaluations"] = new_pending
            params["ml_metrics"] = metrics
            strategy.params = params
            flag_modified(strategy, "params")
            db.commit()

    def _evaluate_grid(self, strategy, current_price, db):
        """
        Simple Grid Logic:
        Params: {"min_price": 50000, "max_price": 60000, "grids": 10, "amount_per_grid": 50}
        """
        # Full grid logic is complex. For this MVP, we will simulate a buy
        # if price drops into a lower grid zone and we don't have an open position there.
        # This is a placeholder for the full implementation.
        return None

    def _execute_trade(self, strategy, order_type, amount, price, db, avg_buy_price=None):
        from app.core.config import settings
        from app.services.exchange_service import get_exchange
        exchange = get_exchange(local_simulation=settings.OBSERVATION_ONLY)
        
        # 1. Place order via ExchangeService (updates virtual balance)
        balance_before = exchange.get_balance()
        
        # For SELL, amount is USDT value to sell
        order = exchange.place_market_order(
            symbol=f"{strategy.ticker}/USDT",
            side=order_type.lower(),
            amount=amount / price
        )
        
        if not order:
            print(f"❌ Failed to execute {order_type} for {strategy.ticker}: Insufficient balance")
            return f"Failed to execute {order_type} for {strategy.ticker}: Insufficient balance"

        balance_after = exchange.get_balance()
        
        # 2. Logging and PnL calculation
        if order_type.upper() == "BUY":
            print(f"📊 BUY {strategy.ticker} | Price: ${price:,.2f} | Amount: {amount:.2f} USDT | Balance: ${balance_before:,.2f} -> ${balance_after:,.2f}")
        else:
            pnl = (price - avg_buy_price) * (amount / price) if avg_buy_price else 0
            pnl_str = f"+{pnl:.2f}" if pnl >= 0 else f"{pnl:.2f}"
            print(f"📉 SELL {strategy.ticker} | Price: ${price:,.2f} | ETH Sold: {amount/price:.6f} | Balance: ${balance_before:,.2f} -> ${balance_after:,.2f} | PnL: {pnl_str} USDT")

        # 3. Record Execution
        execution = StrategyExecution(
            strategy_id=strategy.id,
            order_type=order_type.upper(),
            price=price,
            amount=amount
        )
        db.add(execution)
        
        # 4. Create Paper Trade record
        trade = PaperTrade(
            ticker=strategy.ticker,
            amount=amount / price,
            price=price,
            type=order_type.upper(),
            status="OPEN" if order_type.upper() == "BUY" else "CLOSED",
            pnl=(price - avg_buy_price) * (amount / price) if order_type.upper() == "SELL" and avg_buy_price else 0.0,
            owner_id=strategy.user_id
        )
        db.add(trade)
        db.commit()
        
        return f"Executed {order_type} for {strategy.ticker} at ${price:,.2f} (SIM)"

    def _get_global_portfolio_stats(self, db): # Added db for future use
        """Mock global portfolio stats for Risk Governor."""
        from app.core.config import settings
        from app.services.exchange_service import get_exchange
        exchange = get_exchange(local_simulation=settings.OBSERVATION_ONLY)
        balance = exchange.get_balance()
        
        # Calculate total equity (USDT + Assets)
        # For simplicity, we assume one strategy exists or we query all
        total_equity = balance
        # In a real scenario, we'd query all strategies and assets
        # For now, we use a placeholder ATH or track it
        portfolio_ath = 1000.0 # Placeholder
        
        return {
            "total_equity": total_equity,
            "portfolio_ath": portfolio_ath,
            "drawdown": (portfolio_ath - total_equity) / portfolio_ath if portfolio_ath > 0 else 0
        }
