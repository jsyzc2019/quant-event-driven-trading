use crate::series::Series;
use std::ops::{Add, BitAnd, BitOr, Div, Mul, Neg, Sub};

impl Series<f32> {
    fn binary_op_series<F>(&self, rhs: &Series<f32>, op: F) -> Series<f32>
    where
        F: Fn(&f32, &f32) -> f32,
    {
        self.zip_with(rhs, |a, b| match (a, b) {
            (Some(a_val), Some(b_val)) => Some(op(a_val, b_val)),
            _ => None,
        })
    }

    fn unary_op_scalar<F>(&self, scalar: f32, op: F) -> Series<f32>
    where
        F: Fn(&f32, f32) -> f32,
    {
        self.fmap(|val| val.map(|v| op(v, scalar)))
    }

    pub fn neg(&self) -> Series<f32> {
        self.fmap(|val| val.map(|v| v.neg()))
    }

    pub fn add_series(&self, rhs: &Series<f32>) -> Series<f32> {
        self.binary_op_series(rhs, |a, b| a + b)
    }

    pub fn mul_series(&self, rhs: &Series<f32>) -> Series<f32> {
        self.binary_op_series(rhs, |a, b| a * b)
    }

    pub fn div_series(&self, rhs: &Series<f32>) -> Series<f32> {
        self.zip_with(rhs, |a, b| match (a, b) {
            (Some(a_val), Some(b_val)) if *b_val != 0.0 => Some(a_val / b_val),
            _ => None,
        })
    }

    pub fn sub_series(&self, rhs: &Series<f32>) -> Series<f32> {
        self.binary_op_series(rhs, |a, b| a - b)
    }

    pub fn add_scalar(&self, scalar: f32) -> Series<f32> {
        self.unary_op_scalar(scalar, |v, s| v + s)
    }

    pub fn mul_scalar(&self, scalar: f32) -> Series<f32> {
        self.unary_op_scalar(scalar, |v, s| v * s)
    }

    pub fn div_scalar(&self, scalar: f32) -> Series<f32> {
        self.unary_op_scalar(scalar, |v, s| if s != 0.0 { v / s } else { 0.0 })
    }

    pub fn sub_scalar(&self, scalar: f32) -> Series<f32> {
        self.unary_op_scalar(scalar, |v, s| v - s)
    }
}

impl Neg for &Series<f32> {
    type Output = Series<f32>;

    fn neg(self) -> Series<f32> {
        self.neg()
    }
}

impl Series<bool> {
    fn bool_op_series<F>(&self, rhs: &Series<f32>, op: F) -> Series<f32>
    where
        F: Fn(&bool, &f32) -> f32,
    {
        self.zip_with(rhs, |b, a| match (b, a) {
            (Some(b_val), Some(a_val)) => Some(op(b_val, a_val)),
            _ => None,
        })
    }

    pub fn mul_series(&self, rhs: &Series<f32>) -> Series<f32> {
        self.bool_op_series(rhs, |b, a| if *b { *a } else { 0.0 })
    }
}

macro_rules! impl_series_ops {
    ($trait_name:ident, $trait_method:ident, $method:ident) => {
        impl $trait_name<Series<f32>> for &Series<f32> {
            type Output = Series<f32>;
            fn $trait_method(self, rhs: Series<f32>) -> Self::Output {
                self.$method(&rhs)
            }
        }

        impl $trait_name<&Series<f32>> for Series<f32> {
            type Output = Series<f32>;
            fn $trait_method(self, rhs: &Series<f32>) -> Self::Output {
                self.$method(rhs)
            }
        }

        impl $trait_name<&Series<f32>> for &Series<f32> {
            type Output = Series<f32>;
            fn $trait_method(self, rhs: &Series<f32>) -> Self::Output {
                self.$method(rhs)
            }
        }

        impl $trait_name<Series<f32>> for Series<f32> {
            type Output = Series<f32>;
            fn $trait_method(self, rhs: Series<f32>) -> Self::Output {
                self.$method(&rhs)
            }
        }
    };
}

impl_series_ops!(Add, add, add_series);
impl_series_ops!(Mul, mul, mul_series);
impl_series_ops!(Div, div, div_series);
impl_series_ops!(Sub, sub, sub_series);

macro_rules! impl_scalar_ops {
    ($trait_name:ident, $trait_method:ident, $method:ident) => {
        impl $trait_name<&Series<f32>> for f32 {
            type Output = Series<f32>;
            fn $trait_method(self, rhs: &Series<f32>) -> Self::Output {
                rhs.$method(self)
            }
        }

        impl $trait_name<Series<f32>> for f32 {
            type Output = Series<f32>;
            fn $trait_method(self, rhs: Series<f32>) -> Self::Output {
                rhs.$method(self)
            }
        }

        impl $trait_name<f32> for &Series<f32> {
            type Output = Series<f32>;
            fn $trait_method(self, scalar: f32) -> Self::Output {
                self.$method(scalar)
            }
        }

        impl $trait_name<f32> for Series<f32> {
            type Output = Series<f32>;
            fn $trait_method(self, scalar: f32) -> Self::Output {
                self.$method(scalar)
            }
        }
    };
}

impl Div<f32> for &Series<f32> {
    type Output = Series<f32>;

    fn div(self, scalar: f32) -> Self::Output {
        self.div_scalar(scalar)
    }
}

impl Div<f32> for Series<f32> {
    type Output = Series<f32>;

    fn div(self, scalar: f32) -> Self::Output {
        self.div_scalar(scalar)
    }
}

impl Div<&Series<f32>> for f32 {
    type Output = Series<f32>;

    fn div(self, rhs: &Series<f32>) -> Self::Output {
        Series::fill(self, rhs.len()).div_series(rhs)
    }
}

impl Div<Series<f32>> for f32 {
    type Output = Series<f32>;

    fn div(self, rhs: Series<f32>) -> Self::Output {
        Series::fill(self, rhs.len()).div_series(&rhs)
    }
}

impl Sub<f32> for &Series<f32> {
    type Output = Series<f32>;

    fn sub(self, scalar: f32) -> Self::Output {
        self.sub_scalar(scalar)
    }
}

impl Sub<f32> for Series<f32> {
    type Output = Series<f32>;

    fn sub(self, scalar: f32) -> Self::Output {
        self.sub_scalar(scalar)
    }
}

impl Sub<&Series<f32>> for f32 {
    type Output = Series<f32>;

    fn sub(self, rhs: &Series<f32>) -> Self::Output {
        rhs.neg().sub_scalar(-self)
    }
}

impl Sub<Series<f32>> for f32 {
    type Output = Series<f32>;

    fn sub(self, rhs: Series<f32>) -> Self::Output {
        rhs.neg().sub_scalar(-self)
    }
}

impl_scalar_ops!(Add, add, add_scalar);
impl_scalar_ops!(Mul, mul, mul_scalar);

macro_rules! impl_bool_ops {
    ($trait_name:ident, $trait_method:ident, $method:ident) => {
        impl $trait_name<&Series<f32>> for &Series<bool> {
            type Output = Series<f32>;
            fn $trait_method(self, rhs: &Series<f32>) -> Self::Output {
                self.$method(&rhs)
            }
        }

        impl $trait_name<&Series<f32>> for Series<bool> {
            type Output = Series<f32>;
            fn $trait_method(self, rhs: &Series<f32>) -> Self::Output {
                self.$method(rhs)
            }
        }
    };
}

impl_bool_ops!(Mul, mul, mul_series);

impl Series<bool> {
    fn logical_op<F>(&self, rhs: &Series<bool>, operation: F) -> Series<bool>
    where
        F: Fn(bool, bool) -> bool,
    {
        self.zip_with(rhs, |a, b| match (a, b) {
            (Some(a_val), Some(b_val)) => Some(operation(*a_val, *b_val)),
            _ => None,
        })
    }
}

impl BitAnd for Series<bool> {
    type Output = Self;

    fn bitand(self, rhs: Self) -> Self::Output {
        self.logical_op(&rhs, |a, b| a & b)
    }
}

impl BitOr for Series<bool> {
    type Output = Self;

    fn bitor(self, rhs: Self) -> Self::Output {
        self.logical_op(&rhs, |a, b| a | b)
    }
}
