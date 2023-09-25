use core::{iff, Series};

pub fn rsi(source: &Series<f32>, period: usize) -> Series<f32> {
    let len = source.len();

    let mom = source.change(1);
    let up = mom.smax(0.0).smma(period);
    let down = mom.smin(0.0).neg().smma(period);

    let oneh = Series::fill(len, 100.0);
    let zero = Series::fill(len, 0.0);

    iff!(
        down.seq(0.0),
        oneh,
        iff!(up.seq(0.0), zero, 100.0 - 100.0 / (1.0 + up / down))
    )
}

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn test_rsi_with_valid_data() {
        let source = Series::from([
            44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84,
        ]);
        let epsilon = 0.001;
        let period = 6;
        let expected = [
            100.0, 0.0, 22.3602, 6.5478, 56.1559, 69.602_67, 74.642_23, 79.480_51, 84.221_98,
        ];

        let result: Vec<f32> = rsi(&source, period).into();

        for i in 0..source.len() {
            assert!(
                (result[i] - expected[i]).abs() < epsilon,
                "at position {}: {} != {}",
                i,
                result[i],
                expected[i]
            )
        }
    }
}
