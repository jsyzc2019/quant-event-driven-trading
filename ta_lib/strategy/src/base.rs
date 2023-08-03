use price::{average::average_price, median::median_price, typical::typical_price, wcl::wcl};
use std::{
    cmp::min,
    collections::{HashMap, VecDeque},
};

pub struct OHLCV {
    pub open: f64,
    pub high: f64,
    pub low: f64,
    pub close: f64,
    pub volume: f64,
}

pub struct OHLCVSeries {
    pub open: Vec<f64>,
    pub high: Vec<f64>,
    pub low: Vec<f64>,
    pub close: Vec<f64>,
    pub volume: Vec<f64>,
}

impl OHLCVSeries {
    fn new(data: &VecDeque<OHLCV>) -> OHLCVSeries {
        OHLCVSeries {
            open: data.iter().map(|ohlcv| ohlcv.open).collect(),
            high: data.iter().map(|ohlcv| ohlcv.high).collect(),
            low: data.iter().map(|ohlcv| ohlcv.low).collect(),
            close: data.iter().map(|ohlcv| ohlcv.close).collect(),
            volume: data.iter().map(|ohlcv| ohlcv.volume).collect(),
        }
    }
}

trait Price {
    fn hl2(&self) -> Vec<f64>;
    fn hlc3(&self) -> Vec<f64>;
    fn hlcc4(&self) -> Vec<f64>;
    fn ohlc4(&self) -> Vec<f64>;
}

impl Price for OHLCVSeries {
    fn hl2(&self) -> Vec<f64> {
        median_price(&self.high, &self.low)
    }

    fn hlc3(&self) -> Vec<f64> {
        typical_price(&self.high, &self.low, &self.close)
    }

    fn hlcc4(&self) -> Vec<f64> {
        wcl(&self.high, &self.low, &self.close)
    }

    fn ohlc4(&self) -> Vec<f64> {
        average_price(&self.open, &self.high, &self.low, &self.close)
    }
}

#[repr(u32)]
pub enum Action {
    GoLong = 1,
    GoShort = 2,
    ExitLong = 3,
    ExitShort = 4,
    DoNothing = 0,
}

pub trait Strategy {
    const DEFAULT_LOOKBACK: usize = 55;

    fn next(&mut self, data: OHLCV) -> Action;
    fn can_process(&self) -> bool;
    fn params(&self) -> HashMap<String, usize>;
    fn entry(&self, data: &OHLCVSeries) -> (bool, bool);
    fn exit(&self, data: &OHLCVSeries) -> (bool, bool);
}

pub struct BaseStrategy {
    data: VecDeque<OHLCV>,
    lookback_period: usize,
}

impl BaseStrategy {
    pub fn new(lookback_period: usize) -> BaseStrategy {
        let lookback_period = min(lookback_period, Self::DEFAULT_LOOKBACK);

        BaseStrategy {
            data: VecDeque::with_capacity(lookback_period),
            lookback_period,
        }
    }
}

impl Strategy for BaseStrategy {
    fn next(&mut self, data: OHLCV) -> Action {
        self.data.push_back(data);

        if self.data.len() > self.lookback_period {
            self.data.pop_front();
        }

        if self.can_process() {
            let series = OHLCVSeries::new(&self.data);

            let (go_long, go_short) = self.entry(&series);
            let (exit_long, exit_short) = self.exit(&series);

            if go_long {
                return Action::GoLong;
            }

            if go_short {
                return Action::GoShort;
            }

            if exit_long {
                return Action::ExitLong;
            }

            if exit_short {
                return Action::ExitShort;
            }
        }

        Action::DoNothing
    }

    fn can_process(&self) -> bool {
        self.data.len() == self.lookback_period
    }

    fn params(&self) -> HashMap<String, usize> {
        let mut map = HashMap::new();
        map.insert(String::from("lookback_period"), self.lookback_period);

        map
    }

    fn entry(&self, _series: &OHLCVSeries) -> (bool, bool) {
        (false, false)
    }

    fn exit(&self, _series: &OHLCVSeries) -> (bool, bool) {
        (false, false)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_base_strategy_creation() {
        let strategy = BaseStrategy::new(20);
        assert_eq!(strategy.lookback_period, 20);
    }

    #[test]
    fn test_base_strategy_can_process() {
        let mut strategy = BaseStrategy::new(2);
        assert_eq!(strategy.can_process(), false);

        strategy.next(OHLCV {
            open: 1.0,
            high: 2.0,
            low: 1.0,
            close: 2.0,
            volume: 1000.0,
        });
        assert_eq!(strategy.can_process(), false);

        strategy.next(OHLCV {
            open: 2.0,
            high: 3.0,
            low: 2.0,
            close: 3.0,
            volume: 2000.0,
        });
        assert_eq!(strategy.can_process(), true);
    }

    #[test]
    fn test_base_strategy_params() {
        let strategy = BaseStrategy::new(20);
        let params = strategy.params();
        assert_eq!(params.get("lookback_period"), Some(&20));
    }

    #[test]
    fn test_strategy_data() {
        let mut strategy = BaseStrategy::new(3);
        let ohlcvs = vec![
            OHLCV {
                open: 1.0,
                high: 2.0,
                low: 0.5,
                close: 1.5,
                volume: 100.0,
            },
            OHLCV {
                open: 2.0,
                high: 3.0,
                low: 1.5,
                close: 2.5,
                volume: 200.0,
            },
            OHLCV {
                open: 3.0,
                high: 4.0,
                low: 2.5,
                close: 3.5,
                volume: 300.0,
            },
            OHLCV {
                open: 4.0,
                high: 5.0,
                low: 3.5,
                close: 4.5,
                volume: 400.0,
            },
        ];

        for ohlcv in ohlcvs {
            strategy.next(ohlcv);
        }

        let series = OHLCVSeries::new(&strategy.data);

        assert_eq!(series.open, vec![2.0, 3.0, 4.0]);
        assert_eq!(series.high, vec![3.0, 4.0, 5.0]);
        assert_eq!(series.low, vec![1.5, 2.5, 3.5]);
        assert_eq!(series.close, vec![2.5, 3.5, 4.5]);
        assert_eq!(series.volume, vec![200.0, 300.0, 400.0]);

        assert_eq!(series.hl2(), vec![2.25, 3.25, 4.25]);
        assert_eq!(
            series.hlc3(),
            vec![2.3333333333333335, 3.3333333333333335, 4.333333333333333]
        );
        assert_eq!(series.hlcc4(), vec![2.375, 3.375, 4.375]);
        assert_eq!(series.ohlc4(), vec![2.25, 3.25, 4.25]);
    }
}