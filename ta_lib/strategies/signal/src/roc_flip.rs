use base::prelude::*;
use core::prelude::*;
use momentum::roc;

pub struct ROCFlipSignal {
    period: usize,
}

impl ROCFlipSignal {
    pub fn new(period: f32) -> Self {
        Self {
            period: period as usize,
        }
    }
}

impl Signal for ROCFlipSignal {
    fn lookback(&self) -> usize {
        self.period
    }

    fn generate(&self, data: &OHLCVSeries) -> (Series<bool>, Series<bool>) {
        let roc = roc(&data.close, self.period);

        (roc.cross_over(&ZERO_LINE), roc.cross_under(&ZERO_LINE))
    }
}
