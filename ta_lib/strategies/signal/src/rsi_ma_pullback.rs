use base::prelude::*;
use core::prelude::*;
use momentum::rsi;

const RSI_NEUTRALITY: f32 = 50.0;

pub struct RSIMaPullbackSignal {
    smooth_type: Smooth,
    rsi_period: usize,
    smooth_signal: Smooth,
    smoothing_period: usize,
    threshold: f32,
}

impl RSIMaPullbackSignal {
    pub fn new(
        smooth_type: Smooth,
        rsi_period: f32,
        smooth_signal: Smooth,
        smoothing_period: f32,
        threshold: f32,
    ) -> Self {
        Self {
            smooth_type,
            rsi_period: rsi_period as usize,
            smooth_signal,
            smoothing_period: smoothing_period as usize,
            threshold,
        }
    }
}

impl Signal for RSIMaPullbackSignal {
    fn lookback(&self) -> usize {
        std::cmp::max(self.rsi_period, self.smoothing_period)
    }

    fn generate(&self, data: &OHLCVSeries) -> (Series<bool>, Series<bool>) {
        let rsi = rsi(&data.close, self.smooth_type, self.rsi_period);
        let rsi_ma = rsi.smooth(self.smooth_signal, self.smoothing_period);
        let upper_neutrality = RSI_NEUTRALITY + self.threshold;
        let lower_neutrality = RSI_NEUTRALITY - self.threshold;

        (
            rsi.sgt(&rsi_ma)
                & rsi.slt(&upper_neutrality)
                & rsi.shift(1).seq(&rsi_ma.shift(1))
                & rsi.shift(2).sgt(&rsi.shift(1))
                & rsi.shift(3).slt(&rsi_ma.shift(3)),
            rsi.slt(&rsi_ma)
                & rsi.sgt(&lower_neutrality)
                & rsi.shift(1).seq(&rsi_ma.shift(1))
                & rsi.shift(2).slt(&rsi.shift(1))
                & rsi.shift(3).sgt(&rsi_ma.shift(3)),
        )
    }
}
