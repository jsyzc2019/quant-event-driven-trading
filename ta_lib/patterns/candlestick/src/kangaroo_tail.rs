use core::prelude::*;

pub fn bullish(
    open: &Series<f32>,
    high: &Series<f32>,
    low: &Series<f32>,
    close: &Series<f32>,
) -> Series<bool> {
    let range = high - low;
    let two_third_low_range = low + &range * 0.66;

    close.sgt(&two_third_low_range)
        & open.sgt(&two_third_low_range)
        & close.sgt(&low.shift(1))
        & close.slt(&high.shift(1))
        & open.sgt(&low.shift(1))
        & open.slt(&high.shift(1))
        & close.slt(&close.shift(200))
        & range.sgt(&range.shift(1))
        & range.sgt(&range.shift(2))
        & range.sgt(&range.shift(3))
        & close.shift(1).slt(&open.shift(2))
        & low.sle(&low.lowest(13))
}

pub fn bearish(
    open: &Series<f32>,
    high: &Series<f32>,
    low: &Series<f32>,
    close: &Series<f32>,
) -> Series<bool> {
    let range = high - low;
    let two_third_high_range = high - &range * 0.66;

    close.slt(&two_third_high_range)
        & open.slt(&two_third_high_range)
        & close.sgt(&low.shift(1))
        & close.slt(&high.shift(1))
        & open.sgt(&low.shift(1))
        & open.slt(&high.shift(1))
        & close.sgt(&close.shift(200))
        & range.sgt(&range.shift(1))
        & range.sgt(&range.shift(2))
        & range.sgt(&range.shift(3))
        & close.shift(1).sgt(&open.shift(2))
        & high.sle(&high.lowest(13))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_kangaroo_tail_bullish() {
        let open = Series::from([4.0; 201]);
        let high = Series::from([4.5; 201]);
        let low = Series::from([4.0; 201]);
        let close = Series::from([4.5; 201]);
        let expected = vec![false; 201];

        let result: Vec<bool> = bullish(&open, &high, &low, &close).into();

        assert_eq!(result, expected);
    }

    #[test]
    fn test_kangaroo_tail_bearish() {
        let open = Series::from([4.0; 201]);
        let high = Series::from([4.5; 201]);
        let low = Series::from([4.0; 201]);
        let close = Series::from([4.5; 201]);
        let expected = vec![false; 201];

        let result: Vec<bool> = bearish(&open, &high, &low, &close).into();

        assert_eq!(result, expected);
    }
}
