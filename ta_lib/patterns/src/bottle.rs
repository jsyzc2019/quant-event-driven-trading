use core::series::Series;

pub fn bullish(open: &[f64], low: &[f64], close: &[f64]) -> Vec<bool> {
    let open = Series::from(open);
    let low = Series::from(low);
    let close = Series::from(close);

    (close.shift(2).gt_series(&open.shift(2))
        & close.shift(1).gt_series(&open.shift(1))
        & open.shift(1).lt_series(&close.shift(2))
        & open.shift(1).eq_series(&low.shift(1))
        & close.shift(1).gt_series(&close.shift(2)))
    .into()
}

pub fn bearish(open: &[f64], high: &[f64], close: &[f64]) -> Vec<bool> {
    let open = Series::from(open);
    let high = Series::from(high);
    let close = Series::from(close);

    (close.shift(2).lt_series(&open.shift(2))
        & close.shift(1).lt_series(&open.shift(1))
        & open.shift(1).gt_series(&close.shift(2))
        & open.shift(1).eq_series(&high.shift(1))
        & close.shift(1).lt_series(&close.shift(2)))
    .into()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bottle_bullish() {
        let open = vec![4.0, 3.0, 4.0, 3.0, 5.0];
        let low = vec![3.5, 2.5, 3.5, 2.5, 4.5];
        let close = vec![4.5, 4.0, 5.0, 4.5, 5.5];
        let expected = vec![false, false, false, false, false];

        let result = bullish(&open, &low, &close);

        assert_eq!(result, expected);
    }

    #[test]
    fn test_bottle_bearish() {
        let open = vec![4.0, 5.0, 4.0, 5.0, 4.0];
        let high = vec![4.5, 5.5, 4.5, 5.5, 4.5];
        let close = vec![3.5, 4.0, 3.5, 4.0, 3.5];
        let expected = vec![false, false, false, false, false];

        let result = bearish(&open, &high, &close);

        assert_eq!(result, expected);
    }
}
