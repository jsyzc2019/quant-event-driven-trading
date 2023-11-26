use base::{BaseLine, OHLCVSeries};
use core::Series;
use shared::{ma_indicator, MovingAverageType};

pub struct MABaseLine {
    smoothing: MovingAverageType,
    period: usize,
}

impl MABaseLine {
    pub fn new(smoothing: MovingAverageType, period: f32) -> Self {
        Self {
            smoothing,
            period: period as usize,
        }
    }
}

impl BaseLine for MABaseLine {
    fn lookback(&self) -> usize {
        self.period
    }

    fn filter(&self, data: &OHLCVSeries) -> (Series<bool>, Series<bool>) {
        let ma = ma_indicator(&self.smoothing, data, self.period);

        (data.close.gt(&ma), data.close.lt(&ma))
    }
}