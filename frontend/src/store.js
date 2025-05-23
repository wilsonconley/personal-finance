import { writable, derived } from 'svelte/store';

/** Store for your data. 
This assumes the data you're pulling back will be an array.
If it's going to be an object, default this to an empty object.
**/
export const balances = writable([]);
export const transactions = writable([]);
export const link_token = writable([]);
export const is_page_loaded = writable(false);
export const is_bokeh_initialized = writable(false);
export const is_plaid_link_initialized = writable(false);
export const filter_month = writable(-1);
export const filter_year = writable(-1);
export const filter_yearly_transactions = writable(-1);
export const yearly_transactions = writable([]);
export const budget = writable({});
export const rules = writable([]);

// /** Data transformation.
// For our use case, we only care about the drink names, not the other information.
// Here, we'll create a derived store to hold the drink names.
// **/
// export const drinkNames = derived(apiData, ($apiData) => {
//     if ($apiData.drinks) {
//         return $apiData.drinks.map(drink => drink.strDrink);
//     }
//     return [];
// });