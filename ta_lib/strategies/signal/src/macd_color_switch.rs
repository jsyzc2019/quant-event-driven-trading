use base::{OHLCVSeries, Signal};
use core::{Comparator, Series};
use shared::{macd_indicator, MACDType};

const ZERO_LINE: f32 = 0.0;

pub struct MACDColorSwitchSignal {
    macd_type: MACDType,
    fast_period: usize,
    slow_period: usize,
    signal_period: usize,
}

impl MACDColorSwitchSignal {
    pub fn new(
        macd_type: MACDType,
        fast_period: f32,
        slow_period: f32,
        signal_period: f32,
    ) -> Self {
        Self {
            macd_type,
            fast_period: fast_period as usize,
            slow_period: slow_period as usize,
            signal_period: signal_period as usize,
        }
    }
}

impl Signal for MACDColorSwitchSignal {
    fn lookback(&self) -> usize {
        let adj_lookback = std::cmp::max(self.fast_period, self.slow_period);
        std::cmp::max(adj_lookback, self.signal_period)
    }

    fn generate(&self, data: &OHLCVSeries) -> (Series<bool>, Series<bool>) {
        let (_, _, histogram) = macd_indicator(
            &self.macd_type,
            data,
            self.fast_period,
            self.slow_period,
            self.signal_period,
        );

        (
            histogram.sgt(&ZERO_LINE)
                & histogram.sgt(&histogram.shift(1))
                & histogram.shift(1).slt(&histogram.shift(2)),
            histogram.slt(&ZERO_LINE)
                & histogram.slt(&histogram.shift(1))
                & histogram.shift(1).sgt(&histogram.shift(2)),
        )
    }
}
