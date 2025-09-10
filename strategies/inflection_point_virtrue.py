import pandas as pd
from datetime import datetime
from autotrader.strategy import Strategy
from autotrader.brokers.broker import Broker
from autotrader.comms.Enum import Exchange,Direction,Offset
from autotrader.brokers.order import Order

class INFLECTION(Strategy):
    """EMA Crossover example strategy.

    Entry signals are on crosses of two EMA's, with a stop-loss
    set using the ATR.
    """

    def __init__(
        self, parameters: dict, period: str, instrument: str, exchange:Exchange, broker: Broker, *args, **kwargs
    ) -> None:
        """Define all indicators used in the strategy."""
        self.name = "inflection_point"
        self.instrument = instrument
        self.exchange = exchange
        self.parameters = parameters
        self.period = period
        self.broker = broker
        self.position = 0
        self.signal = 0

    def rngfilt(self, price: pd.Series, smoothrng: pd.Series) -> pd.Series:
        filt = pd.Series(index=price.index, dtype='float64')
        filt.iloc[0] = price.iloc[0]

        for i in range(1, len(price)):
            prev = filt.iloc[i - 1]
            r = smoothrng.iloc[i]
            x = price.iloc[i]

            if x > prev:
                filt.iloc[i] = prev if x - r < prev else x - r
            else:
                filt.iloc[i] = prev if x + r > prev else x + r

        return filt

    def create_plotting_indicators(self, data: pd.DataFrame):

        # Construct indicators dict for plotting
        data['middle'] = (data['Open'] + data['Close']) / 2
        diff_ema,ema5,ema20 = self.generate_features(data)
        data['smooth'] =self.rngfilt(data['middle'], diff_ema)


        self.indicators = {

            "SSF": {
                "type": "MA",
                "data": pd.Series(
                            data['smooth'],
                            name="SSF",
                            )
            },
            "Fast EMA": {
                "type": "MA",
                "data": pd.Series(
                    data['middle'].ewm(span=10, adjust=False).mean(),
                    name="Fast EMA",
                )
            },
            "Slow EMA": {
                "type": "MA",
                "data": pd.Series(
                    data['middle'].ewm(span=20, adjust=False).mean(),
                    name="Slow EMA",
                )
            },
        }

    def generate_features(self, data: pd.DataFrame):
        """Calculates the indicators required to run the strategy."""

        # k线差值的ema
        data['middle'] = (data['Open'] + data['Close']) / 2

        wper = 2 * self.parameters["smooth_period"] - 1
        abs_diff = (data['middle'] - data['middle'].shift(1)).abs()
        ema1 = abs_diff.ewm(span=self.parameters["smooth_period"], adjust=False).mean()
        ema2 = ema1.ewm(span=wper, adjust=False).mean()

        ema5 = data['middle'].ewm(span=10, adjust=False).mean()
        ema20 = data['middle'].ewm(span=20, adjust=False).mean()
        diff = (ema1*self.parameters['m'])

        return diff, ema5, ema20


    def generate_signal(self, dt: datetime):
        """Define strategy to determine entry signals."""
        # Get OHLCV data
        count = 105
        data = self.broker.get_candles(self.instrument, granularity=self.period, count=count, end_time=dt) #最新的时间在最后一行
        data['middle'] = (data['Open'] + data['Close'])/2
        if len(data) < 105:
            # This was previously a check in AT
            return None
        data['middle'] = (data['Open'] + data['Close']) / 2

        diff_ema, ema5, ema20 = self.generate_features(data)
        data['smooth'] = self.rngfilt(data['middle'], diff_ema)
        data['s_ema'] = data['smooth'].ewm(span=20, adjust=False).mean()

        if data['smooth'].iloc[-1] > data['smooth'].iloc[-2]:
            self.signal = 1
        elif data['smooth'].iloc[-1] < data['smooth'].iloc[-2]:
            self.signal = -1

        comfirm = 0
        if (ema5.iloc[-1] - ema5.iloc[-2]) > 0:
            comfirm = 1
        elif (ema5.iloc[-1] - ema5.iloc[-2]) < 0:
            comfirm = -1

        position_dicts = self.broker.get_positions(self.instrument)
        position = {}
        if position_dicts:
            for position_dict in position_dicts:
                if position_dict["direction"] == 2:
                    position["long_tdPosition"] = position_dict["tdPosition"]
                    position["long_ydPosition"] = position_dict["ydPosition"]
                    position["openPrice"] = position_dict["openPrice"]
                    position["positionProfit"] = position_dict["positionProfit"]
                elif position_dict["direction"] == 3:
                    position["short_tdPosition"] = position_dict["tdPosition"]
                    position["short_ydPosition"] = position_dict["ydPosition"]
                    position["openPrice"] = position_dict["openPrice"]
                    position["positionProfit"] = position_dict["positionProfit"]

        if not position == 0:
            if self.signal == 1 and comfirm == 1:
                order = Order(
                    instrument=self.instrument,
                    exchange=self.exchange,
                    direction=Direction.Long,  # 买
                    offset=Offset.Open,  # 平今
                    price=3035,
                    size=1
                )
                self.position = 1

            elif self.signal == -1 and comfirm ==-1:
                order = Order(
                    instrument=self.instrument,
                    exchange=self.exchange,
                    direction=Direction.Short,  # 买
                    offset=Offset.CloseToday,  # 平今
                    price=3035,
                    size=1
                )
                self.position = -1

            else:
                # No signal
                order = None
        elif position and (comfirm == -1 or self.signal ==-1):
            order = Order(
                instrument=self.instrument,
                exchange=self.exchange,
                direction=Direction.Short,  # 买
                offset=Offset.Open,  # 平今
                price=3035,
                size=1
            )

            self.position = 0

        elif position and (comfirm == 1 or self.signal == 1):

            order = Order(
                instrument=self.instrument,
                exchange=self.exchange,
                direction=Direction.Long,  # 买
                offset=Offset.Open,  # 平今
                price=3035,
                size=1
            )
            self.position = 0

        else:
            order = None

        return order
    def generate_exit_levels(
        self, signal: int, data: pd.DataFrame, swings: pd.DataFrame
    ):
        """Function to determine stop loss and take profit levels."""
        stop_type = "limit"
        RR = self.parameters["RR"]

        if signal == 0:
            stop = None
            take = None
        else:
            if signal == 1:
                stop = swings["Lows"].iloc[-1]
                take = data["Close"].iloc[-1] + RR * (data["Close"].iloc[-1] - stop)
            else:
                stop = swings["Highs"].iloc[-1]
                take = data["Close"].iloc[-1] - RR * (stop - data["Close"].iloc[-1])

        exit_dict = {"stop_loss": stop, "stop_type": stop_type, "take_profit": take}

        return exit_dict