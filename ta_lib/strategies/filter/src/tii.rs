use base::{Filter, OHLCVSeries};
use core::prelude::*;
use momentum::tii;

const TII_NEUTRALITY: f32 = 50.0;

pub struct TIIFilter {
    major_period: usize,
    minor_period: usize,
    threshold: f32,
}

impl TIIFilter {
    pub fn new(major_period: f32, minor_period: f32, threshold: f32) -> Self {
        Self {
            major_period: major_period as usize,
            minor_period: minor_period as usize,
            threshold,
        }
    }
}

impl Filter for TIIFilter {
    fn lookback(&self) -> usize {
        std::cmp::max(self.major_period, self.minor_period)
    }

    fn confirm(&self, data: &OHLCVSeries) -> (Series<bool>, Series<bool>) {
        let tii = tii(&data.close, self.major_period, self.minor_period);
        let upper_neutrality = TII_NEUTRALITY + self.threshold;
        let lower_neutrality = TII_NEUTRALITY - self.threshold;

        (tii.sge(&upper_neutrality), tii.sle(&lower_neutrality))
    }
}
