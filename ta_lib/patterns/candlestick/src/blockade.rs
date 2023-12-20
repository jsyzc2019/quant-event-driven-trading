use core::prelude::*;

pub fn bullish(
    open: &Series<f32>,
    high: &Series<f32>,
    low: &Series<f32>,
    close: &Series<f32>,
) -> Series<bool> {
    close.shift(1).sgt(&open.shift(1))
        & close.shift(4).slt(&open.shift(4))
        & low.shift(1).sge(&low.shift(4))
        & low.shift(1).sle(&close.shift(4))
        & close.shift(1).sgt(&high.shift(4))
        & low.shift(2).sge(&low.shift(4))
        & low.shift(2).sle(&close.shift(4))
        & low.shift(3).sge(&low.shift(4))
        & low.shift(3).sle(&close.shift(4))
        & high.shift(2).slt(&high.shift(4))
        & high.shift(3).slt(&high.shift(4))
}

pub fn bearish(
    open: &Series<f32>,
    high: &Series<f32>,
    low: &Series<f32>,
    close: &Series<f32>,
) -> Series<bool> {
    close.shift(1).slt(&open.shift(1))
        & close.shift(4).sgt(&open.shift(4))
        & high.shift(1).sle(&high.shift(4))
        & high.shift(1).sge(&close.shift(4))
        & close.shift(1).slt(&low.shift(4))
        & high.shift(2).sle(&high.shift(4))
        & high.shift(2).sge(&close.shift(4))
        & high.shift(3).sle(&high.shift(4))
        & high.shift(3).sge(&close.shift(4))
        & low.shift(2).sgt(&low.shift(4))
        & low.shift(3).sgt(&low.shift(4))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_blockade_bullish() {
        let open = Series::from([4.0, 3.0, 4.0, 3.0, 4.0]);
        let high = Series::from([4.5, 3.5, 4.5, 3.5, 4.5]);
        let low = Series::from([4.0, 3.0, 4.0, 3.0, 4.0]);
        let close = Series::from([4.5, 3.5, 4.5, 3.5, 4.5]);
        let expected = vec![false, false, false, false, false];

        let result: Vec<bool> = bullish(&open, &high, &low, &close).into();

        assert_eq!(result, expected);
    }

    #[test]
    fn test_blockade_bearish() {
        let open = Series::from([4.0, 3.0, 4.0, 3.0, 4.0]);
        let high = Series::from([4.0, 3.0, 4.0, 3.0, 4.0]);
        let low = Series::from([3.5, 2.5, 3.5, 2.5, 3.5]);
        let close = Series::from([3.5, 2.5, 3.5, 2.5, 3.5]);
        let expected = vec![false, false, false, false, false];

        let result: Vec<bool> = bearish(&open, &high, &low, &close).into();

        assert_eq!(result, expected);
    }
}
