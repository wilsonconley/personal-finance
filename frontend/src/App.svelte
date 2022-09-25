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
  } from "./store.js";
  import SvelteTable from "svelte-table";

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

  const balances_cols = [
    { key: "name", title: "Name", value: (v) => v.name, sortable: true },
    {
      key: "balances",
      title: "Balance",
      value: (v) => v.balances_str,
      sortable: true,
    },
  ];

  const transactions_cols = [
    {
      key: "datestr",
      title: "Date",
      value: (v) => v.datestr,
      sortable: true,
      filterOptions: (rows) => {
        return get_unique_values(rows, "datestr");
      },
    },
    {
      key: "amount",
      title: "Amount",
      value: (v) => v.amount,
      sortable: true,
      filterOptions: (rows) => {
        return get_unique_values(rows, "amount");
      },
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
    const response = await fetch("http://127.0.0.1:8000/transactions/");
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
  }

  async function refresh_and_update() {
    // refresh data
    await fetch("http://127.0.0.1:8000/refresh_data/");

    // get balances
    await get_balances();

    // get transactions
    await get_transactions();
  }

  async function make_plots() {
    var response = await fetch("http://127.0.0.1:8000/plot_balances/");
    var item = JSON.parse(await response.json());
    Bokeh.embed.embed_item(item, "plot_balances");

    response = await fetch("http://127.0.0.1:8000/plot_transactions_in/");
    item = JSON.parse(await response.json());
    Bokeh.embed.embed_item(item, "plot_transactions_in");

    response = await fetch("http://127.0.0.1:8000/plot_transactions_out/");
    item = JSON.parse(await response.json());
    Bokeh.embed.embed_item(item, "plot_transactions_out");

    response = await fetch("http://127.0.0.1:8000/table_balances/");
    item = JSON.parse(await response.json());
    Bokeh.embed.embed_item(item, "table_balances");
  }

  onMount(async () => {
    is_page_loaded.set(false);

    // check existing accounts
    await check_existing_tokens();

    // refresh and update data
    await refresh_and_update();

    // make plots
    await make_plots();

    is_page_loaded.set(true);
  });

  function initialize_bokeh() {
    is_bokeh_initialized.set(true);
  }

  function initialize_plaid_link() {
    is_plaid_link_initialized.set(true);
  }
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

  <div>
    <h1>Transactions Overview</h1>
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

  <div class="card">
    <Counter />
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
