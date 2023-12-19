use base::{Filter, OHLCVSeries};
use core::{Comparator, Series};

pub struct FibFilter {
    period: usize,
}

impl FibFilter {
    pub fn new(period: f32) -> Self {
        Self {
            period: period as usize,
        }
    }
}

impl Filter for FibFilter {
    fn lookback(&self) -> usize {
        self.period
    }

    fn confirm(&self, data: &OHLCVSeries) -> (Series<bool>, Series<bool>) {
        (
            data.high.sgt(&data.low.shift(2))
                & data.high.sgt(&data.low.shift(3))
                & data.high.sgt(&data.low.shift(5))
                & data.high.sgt(&data.low.shift(8))
                & data.high.sgt(&data.low.shift(13)),
            data.low.slt(&data.high.shift(2))
                & data.low.slt(&data.high.shift(3))
                & data.low.slt(&data.high.shift(5))
                & data.low.slt(&data.high.shift(8))
                & data.low.slt(&data.high.shift(13)),
        )
    }
}
