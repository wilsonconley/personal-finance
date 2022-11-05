<script>
  // @ts-nocheck

  import Counter from "./lib/Counter.svelte";
  import { onMount } from "svelte";
  import {
    balances,
    transactions,
    link_token,
    is_page_loaded,
    is_bokeh_initialized,
    is_plaid_link_initialized,
    filter_month,
    filter_year,
    filter_yearly_transactions,
    budget,
  } from "./store.js";
  import SvelteTable from "svelte-table";

  let months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  let filter_month_str;
  let savestore = false;
  let years = ["2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015"];
  let tokens_checked = false;
  let total_budget = 0.0;

  $: if (savestore) {
    sessionStorage.removeItem("filter_month");
    sessionStorage.removeItem("filter_year");
    sessionStorage.removeItem("filter_yearly_transactions");
    sessionStorage.removeItem("tokens_checked");
    window.sessionStorage.setItem(
      "filter_month",
      JSON.stringify($filter_month)
    );
    window.sessionStorage.setItem("filter_year", JSON.stringify($filter_year));
    window.sessionStorage.setItem(
      "filter_yearly_transactions",
      JSON.stringify($filter_yearly_transactions)
    );
    window.sessionStorage.setItem(
      "tokens_checked",
      JSON.stringify(tokens_checked)
    );
  }

  const transactions_cols = [
    {
      key: "datestr",
      title: "Date",
      value: (v) => v.datestr,
      sortable: true,
    },
    {
      key: "amount",
      title: "Amount",
      value: (v) => v.amount,
      sortable: true,
    },
    {
      key: "name",
      title: "Name",
      value: (v) => v.name,
      sortable: true,
      filterOptions: (rows) => {
        return get_unique_values(rows, "name");
      },
    },
    {
      key: "merchant_name",
      title: "Merchant",
      value: (v) => v.merchant_name,
      sortable: true,
      filterOptions: (rows) => {
        return get_unique_values(rows, "merchant_name");
      },
    },
    {
      key: "category",
      title: "Category_Detailed",
      value: (v) => v.category,
      sortable: true,
      filterOptions: (rows) => {
        return get_unique_values(rows, "category");
      },
    },
    {
      key: "personal_finance_category",
      title: "Category_Primary",
      value: (v) => v.personal_finance_category_primary,
      sortable: true,
      filterOptions: (rows) => {
        return get_unique_values(rows, "personal_finance_category_primary");
      },
    },
  ];

  function get_unique_values(rows, field) {
    // get all unique values
    let unique_values = {};
    rows.forEach((row) => {
      let this_value = row[field];
      if (unique_values[this_value] === undefined)
        unique_values[this_value] = {
          name: `${this_value}`,
          value: this_value,
        };
    });
    // fix order
    unique_values = Object.entries(unique_values)
      .sort()
      .reduce((o, [k, v]) => ((o[k] = v), o), {});
    return Object.values(unique_values);
  }

  async function get_link_token() {
    const response = await fetch("http://127.0.0.1:8000/create_link_token/", {
      method: "POST",
    });
    link_token.set(JSON.parse(await response.json()));
  }

  async function link_account_btn() {
    await get_link_token();
    var handler = Plaid.create({
      token: $link_token,
      onSuccess: async function (public_token, metadata) {
        is_page_loaded.set(false);
        await fetch("http://127.0.0.1:8000/exchange_public_token/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ token: public_token }),
        });
        await fetch("http://127.0.0.1:8000/refresh_data/");
        window.location.reload();
      },
      onExit: function (err, metadata) {
        if (err != null) {
          console.log(err);
          console.log(metadata);
        }
      },
    });
    handler.open();
  }

  async function get_balances() {
    const response = await fetch("http://127.0.0.1:8000/balances/");
    balances.set(JSON.parse(await response.json()));
  }

  async function get_transactions() {
    const response = await fetch("http://127.0.0.1:8000/transactions/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        month: String($filter_month + 1),
        year: String($filter_year),
      }),
    });
    transactions.set(JSON.parse(await response.json()));
  }

  async function check_existing_tokens() {
    const response = await fetch(
      "http://127.0.0.1:8000/check_existing_tokens/"
    );
    const bad_tokens = JSON.parse(await response.json());
    bad_tokens.forEach(async (token) => {
      const response = await fetch("http://127.0.0.1:8000/create_link_token/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ token: token }),
      });
      const access_link_token = JSON.parse(await response.json());
      var handler = Plaid.create({
        token: access_link_token,
        onSuccess: function (public_token, metadata) {
          fetch("http://127.0.0.1:8000/exchange_public_token/", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ token: public_token }),
          });
        },
        onExit: function (err, metadata) {
          if (err != null) {
            console.log(err);
            console.log(metadata);
          }
        },
      });
      handler.open();
    });
    tokens_checked = true;
  }

  async function refresh_and_update() {
    // refresh data
    await fetch("http://127.0.0.1:8000/refresh_data/");

    // get balances
    await get_balances();

    // get transactions
    await get_transactions();
  }

  async function get_budget() {
    // get budget
    const response = await fetch("http://127.0.0.1:8000/budget/");
    budget.set(JSON.parse(await response.json()));
    await update_budget();
  }

  async function update_budget() {
    total_budget = 0;
    for (const [category, value] of Object.entries($budget)) {
      if (category != "INCOME") {
        total_budget += parseFloat(value);
      }
    }
  }

  async function update_plot(id, clear_old = true) {
    if (clear_old) {
      const my_node = document.getElementById(id);
      if (my_node != undefined) {
        my_node.innerHTML = "";
      }
    }
    const response = await fetch(`http://127.0.0.1:8000/${id}/`);
    const item = JSON.parse(await response.json());
    Bokeh.embed.embed_item(item, id);
  }

  async function make_plots_and_tables() {
    await update_plot("plot_balances");
    await update_plot("plot_transactions_in");
    await update_plot("plot_transactions_out");
    await update_plot("plot_budget");
    await update_plot("table_balances", false);
  }

  function initialize_bokeh() {
    is_bokeh_initialized.set(true);
  }

  function initialize_plaid_link() {
    is_plaid_link_initialized.set(true);
  }

  async function update_monthly_transactions() {
    // update month and year
    var index = months.findIndex((element) => {
      if (element === filter_month_str) {
        return true;
      }
      return false;
    });
    filter_month.set(index);

    // update transactions
    await get_transactions();
    // is_page_loaded.set(false);
    await update_plot("plot_transactions_in");
    await update_plot("plot_transactions_out");
    await update_plot("plot_budget");
    // is_page_loaded.set(true);
  }

  async function update_yearly_transactions() {
    const response = await fetch("http://127.0.0.1:8000/yearly_transactions/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        month: "",
        year: String($filter_yearly_transactions),
      }),
    });
    yearly_transactions.set(JSON.parse(await response.json()));
  }

  async function set_budget() {
    // call API to store budget in backend
    await fetch("http://127.0.0.1:8000/budget/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        budget: $budget,
      }),
    });
    await update_budget();
    await update_plot("plot_budget");
  }

  onMount(async () => {
    is_page_loaded.set(false);

    // load stores
    let ses = window.sessionStorage.getItem("filter_month");
    if (ses) {
      $filter_month = JSON.parse(ses);
    }
    ses = window.sessionStorage.getItem("filter_year");
    if (ses) {
      $filter_year = JSON.parse(ses);
    }
    ses = window.sessionStorage.getItem("filter_yearly_transactions");
    if (ses) {
      $filter_yearly_transactions = JSON.parse(ses);
    }
    ses = window.sessionStorage.getItem("tokens_checked");
    if (ses) {
      tokens_checked = JSON.parse(ses);
    }
    savestore = true;

    // set filters
    const today = new Date();
    if ($filter_month < 0) {
      filter_month.set(today.getMonth());
    }
    filter_month_str = months[$filter_month];
    if ($filter_year < 0) {
      filter_year.set(String(today.getFullYear()));
    }
    if ($filter_yearly_transactions < 0) {
      filter_yearly_transactions.set(String(today.getFullYear()));
    }

    // check existing accounts
    if (!tokens_checked) {
      await check_existing_tokens();
    }

    // refresh and update data
    await refresh_and_update();

    // get budget
    await get_budget();

    // make all plots and tables
    await make_plots_and_tables();

    is_page_loaded.set(true);
  });
</script>

<svelte:head>
  {#if !$is_plaid_link_initialized}
    <script
      src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"
      on:load={initialize_plaid_link}>
    </script>
  {/if}
  <script
    src="https://cdn.bokeh.org/bokeh/release/bokeh-2.4.3.min.js"
    crossorigin="anonymous"
    on:load={initialize_bokeh}>
  </script>
  {#if $is_bokeh_initialized}
    <script
      src="https://cdn.bokeh.org/bokeh/release/bokeh-widgets-2.4.3.min.js"
      crossorigin="anonymous">
    </script>
    <script
      src="https://cdn.bokeh.org/bokeh/release/bokeh-tables-2.4.3.min.js"
      crossorigin="anonymous">
    </script>
    <script
      src="https://cdn.bokeh.org/bokeh/release/bokeh-api-2.4.3.min.js"
      crossorigin="anonymous">
    </script>
    <script
      src="https://cdn.bokeh.org/bokeh/release/bokeh-gl-2.4.3.min.js"
      crossorigin="anonymous">
    </script>
    <script
      src="https://cdn.bokeh.org/bokeh/release/bokeh-mathjax-2.4.3.min.js"
      crossorigin="anonymous">
    </script>
  {/if}
</svelte:head>

<main>
  {#if !$is_page_loaded}
    <div class="loader">Loading...</div>
  {/if}

  <button id="link-button" on:click={link_account_btn}> Link Account </button>

  <div>
    <h1>Account Balances Overview</h1>
    <div id="plot_balances" class="balances_overview" />
    <div id="table_balances" class="balances_table" />
  </div>

  <h1>Budget (Monthly)</h1>
  <div class="arrange-horizontally">
    <div class="budget-summary">
      <p>Income is <span style="color:green">${$budget["INCOME"]}</span></p>
      <p>Budget is <span style="color:red">${total_budget}</span></p>
      <p>
        Savings is <span style="color:yellow"
          >${$budget["INCOME"] - total_budget}</span
        >
      </p>
    </div>
    <div class="budget">
      {#each Object.entries($budget) as [category, value]}
        <div>
          <label for="budget_{category}">{category}:</label>
          <input
            bind:value={$budget[category]}
            on:change={set_budget}
            id="budget_{category}"
            name="budget_{category}"
            placeholder={value}
          />
        </div>
      {/each}
    </div>
  </div>

  <div>
    <h1>Transactions Overview</h1>
    <!-- <h2>Yearly</h2>
    <select
      bind:value={$filter_yearly_transactions}
      on:change={update_yearly_transactions}
    >
      {#each years as year}
        <option value={year}>
          {year}
        </option>
      {/each}
    </select> -->
    <h2>Monthly</h2>
    <div class="arrange-horizontally">
      <select
        bind:value={filter_month_str}
        on:change={update_monthly_transactions}
      >
        {#each months as month}
          <option value={month}>
            {month}
          </option>
        {/each}
      </select>
      <select bind:value={$filter_year} on:change={update_monthly_transactions}>
        {#each years as year}
          <option value={year}>
            {year}
          </option>
        {/each}
      </select>
    </div>
    <div>
      <h3>Budget</h3>
      <div id="plot_budget" class="plot_budget" />
    </div>
    <div class="arrange-horizontally">
      <div>
        <h3>Transactions Out</h3>
        <div id="plot_transactions_out" class="transactions_out" />
      </div>
      <div>
        <h3>Transactions In</h3>
        <div id="plot_transactions_in" class="transactions_in" />
      </div>
    </div>
    <SvelteTable columns={transactions_cols} rows={$transactions} />
  </div>
</main>

<style>
  .balances_overview {
    width: 700px;
    height: auto;
    margin: 0 auto;
    position: relative;
  }
  .balances_table {
    width: 700px;
    height: 200px;
    margin: 0 auto;
    position: relative;
    background-color: white;
    color: black;
  }
  .plot_budget {
    width: 700px;
    height: auto;
    margin: 0 auto;
    position: relative;
  }
  .transactions_out {
    width: 350px;
    height: auto;
    margin: 0 auto;
    position: relative;
  }
  .transactions_in {
    width: 350px;
    height: auto;
    margin: 0 auto;
    position: relative;
  }
  .arrange-horizontally > * {
    display: inline-block;
    text-align: center;
  }
  .budget-summary {
    width: 200px;
    height: auto;
    margin: 0 auto;
    position: relative;
  }
  .budget {
    text-align: right;
    width: 500px;
    height: auto;
    margin: 0 auto;
    position: relative;
  }
  .loader {
    position: fixed;
    top: 0;
    bottom: 0;
    right: 0;
    left: 0;
    display: grid;
    place-items: center;
    background-color: white;
    color: black;
    z-index: 9999;
  }
</style>
