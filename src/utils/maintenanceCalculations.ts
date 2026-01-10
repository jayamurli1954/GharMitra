import {
  Flat,
  WaterExpense,
  FixedExpense,
  MaintenanceBill,
  ApartmentSettings,
} from '../types/models';

/**
 * Calculate maintenance using Square Feet Rate method
 */
export const calculateSqftRateMaintenance = (
  flat: Flat,
  sqftRate: number,
  month: string,
  year: number,
): Partial<MaintenanceBill> => {
  const sqftCharges = flat.area * sqftRate;

  return {
    flatId: flat.id,
    flatNumber: flat.flatNumber,
    month,
    year,
    calculationMethod: 'sqft_rate',
    area: flat.area,
    sqftRate,
    sqftCharges,
    totalAmount: sqftCharges,
    breakdown: {
      calculations: `Area: ${flat.area} sq ft × Rate: ₹${sqftRate} = ₹${sqftCharges}`,
    },
  };
};

/**
 * Calculate maintenance using Variable method
 */
export const calculateVariableMaintenance = (
  flat: Flat,
  waterExpense: WaterExpense,
  fixedExpenses: FixedExpense[],
  sinkingFund: number,
  totalFlats: number,
  month: string,
  year: number,
): Partial<MaintenanceBill> => {
  // Calculate water charges for this flat
  const perPersonWaterCharge = waterExpense.perPersonCharge;
  const waterCharges = perPersonWaterCharge * flat.numberOfOccupants;

  // Calculate fixed expenses per flat
  const monthlyFixedExpenses = fixedExpenses
    .filter(exp => exp.isActive)
    .reduce((total, exp) => {
      if (exp.frequency === 'monthly') {
        return total + exp.amount;
      } else if (exp.frequency === 'quarterly') {
        return total + exp.amount / 3;
      } else if (exp.frequency === 'annual') {
        return total + exp.amount / 12;
      }
      return total;
    }, 0);

  const fixedExpensesPerFlat = monthlyFixedExpenses / totalFlats;
  const sinkingFundPerFlat = sinkingFund / totalFlats;

  const totalAmount = waterCharges + fixedExpensesPerFlat + sinkingFundPerFlat;

  return {
    flatId: flat.id,
    flatNumber: flat.flatNumber,
    month,
    year,
    calculationMethod: 'variable',
    waterCharges,
    fixedExpenses: fixedExpensesPerFlat,
    sinkingFund: sinkingFundPerFlat,
    totalAmount,
    breakdown: {
      waterExpenses: {
        totalOccupants: waterExpense.totalOccupants,
        perPersonCharge: perPersonWaterCharge,
        flatOccupants: flat.numberOfOccupants,
        amount: waterCharges,
      },
      fixedExpensesList: fixedExpenses
        .filter(exp => exp.isActive)
        .map(exp => ({
          name: exp.name,
          amount:
            exp.frequency === 'monthly'
              ? exp.amount / totalFlats
              : exp.frequency === 'quarterly'
              ? exp.amount / 3 / totalFlats
              : exp.amount / 12 / totalFlats,
        })),
      calculations: `
Water: ₹${perPersonWaterCharge.toFixed(2)} × ${flat.numberOfOccupants} occupants = ₹${waterCharges.toFixed(2)}
Fixed Expenses: ₹${monthlyFixedExpenses.toFixed(2)} ÷ ${totalFlats} flats = ₹${fixedExpensesPerFlat.toFixed(2)}
Sinking Fund: ₹${sinkingFund.toFixed(2)} ÷ ${totalFlats} flats = ₹${sinkingFundPerFlat.toFixed(2)}
Total: ₹${totalAmount.toFixed(2)}
      `.trim(),
    },
  };
};

/**
 * Calculate water expense per person
 */
export const calculateWaterExpensePerPerson = (
  tankerCharges: number,
  governmentCharges: number,
  otherCharges: number,
  totalOccupants: number,
): number => {
  const totalWaterExpense = tankerCharges + governmentCharges + otherCharges;
  return totalWaterExpense / totalOccupants;
};

/**
 * Format month-year for display
 */
export const formatMonthYear = (month: string): string => {
  const [year, monthNum] = month.split('-');
  const date = new Date(parseInt(year), parseInt(monthNum) - 1);
  return date.toLocaleDateString('en-IN', {month: 'long', year: 'numeric'});
};

/**
 * Get current month in YYYY-MM format
 */
export const getCurrentMonth = (): string => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}`;
};

/**
 * Parse month string to year and month number
 */
export const parseMonthString = (monthStr: string): {year: number; month: number} => {
  const [year, month] = monthStr.split('-');
  return {
    year: parseInt(year),
    month: parseInt(month),
  };
};

/**
 * Format currency in Indian format
 */
export const formatCurrency = (amount: number): string => {
  return `₹${amount.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
};

/**
 * Generate maintenance bills for all flats
 */
export const generateBillsForAllFlats = async (
  flats: Flat[],
  settings: ApartmentSettings,
  waterExpense: WaterExpense | null,
  fixedExpenses: FixedExpense[],
  month: string,
  year: number,
): Promise<Partial<MaintenanceBill>[]> => {
  const bills: Partial<MaintenanceBill>[] = [];

  if (settings.calculationMethod === 'sqft_rate') {
    // Sqft rate method
    if (!settings.sqftRate) {
      throw new Error('Square feet rate not configured');
    }

    for (const flat of flats) {
      const bill = calculateSqftRateMaintenance(
        flat,
        settings.sqftRate,
        month,
        year,
      );
      bills.push(bill);
    }
  } else {
    // Variable method
    if (!waterExpense) {
      throw new Error('Water expense not entered for this month');
    }

    for (const flat of flats) {
      const bill = calculateVariableMaintenance(
        flat,
        waterExpense,
        fixedExpenses,
        settings.sinkingFundAmount || 0,
        settings.totalFlats,
        month,
        year,
      );
      bills.push(bill);
    }
  }

  return bills;
};
