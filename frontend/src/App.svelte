<script>
  // @ts-nocheck

  import balances_overview from "./assets/balances.svg";
  import transactions_out from "./assets/transactions_out.svg";
  import transactions_in from "./assets/transactions_in.svg";
  import Counter from "./lib/Counter.svelte";
  import { onMount } from "svelte";
  import { balances, transactions, link_token } from "./store.js";
  import SvelteTable from "svelte-table";

  const rows = [
    /** data (example below) */
    { id: 1, first_name: "Marilyn", last_name: "Monroe", pet: "dog" },
    { id: 2, first_name: "Abraham", last_name: "Lincoln", pet: "dog" },
    { id: 3, first_name: "Mother", last_name: "Teresa", pet: "" },
    { id: 4, first_name: "John F.", last_name: "Kennedy", pet: "dog" },
    { id: 5, first_name: "Martin Luther", last_name: "King", pet: "dog" },
    { id: 6, first_name: "Nelson", last_name: "Mandela", pet: "cat" },
    { id: 7, first_name: "Winston", last_name: "Churchill", pet: "cat" },
    { id: 8, first_name: "George", last_name: "Soros", pet: "bird" },
    { id: 9, first_name: "Bill", last_name: "Gates", pet: "cat" },
    { id: 10, first_name: "Muhammad", last_name: "Ali", pet: "dog" },
    { id: 11, first_name: "Mahatma", last_name: "Gandhi", pet: "bird" },
    { id: 12, first_name: "Margaret", last_name: "Thatcher", pet: "cat" },
    { id: 13, first_name: "Christopher", last_name: "Columbus", pet: "dog" },
    { id: 14, first_name: "Charles", last_name: "Darwin", pet: "dog" },
    { id: 15, first_name: "Elvis", last_name: "Presley", pet: "dog" },
    { id: 16, first_name: "Albert", last_name: "Einstein", pet: "dog" },
    { id: 17, first_name: "Paul", last_name: "McCartney", pet: "cat" },
    { id: 18, first_name: "Queen", last_name: "Victoria", pet: "dog" },
    { id: 19, first_name: "Pope", last_name: "Francis", pet: "cat" },
  ];

  const columns = [
    /** columns config (example below) */
    {
      key: "id",
      title: "ID",
      value: (v) => v.id,
      sortable: true,
      filterOptions: (rows) => {
        // generate groupings of 0-10, 10-20 etc...
        let nums = {};
        rows.forEach((row) => {
          let num = Math.floor(row.id / 10);
          if (nums[num] === undefined)
            nums[num] = {
              name: `${num * 10} to ${(num + 1) * 10}`,
              value: num,
            };
        });
        // fix order
        nums = Object.entries(nums)
          .sort()
          .reduce((o, [k, v]) => ((o[k] = v), o), {});
        return Object.values(nums);
      },
      filterValue: (v) => Math.floor(v.id / 10),
      headerClass: "text-left",
    },
    {
      key: "first_name",
      title: "FIRST_NAME",
      value: (v) => v.first_name,
      sortable: true,
      filterOptions: (rows) => {
        // use first letter of first_name to generate filter
        let letrs = {};
        rows.forEach((row) => {
          let letr = row.first_name.charAt(0);
          if (letrs[letr] === undefined)
            letrs[letr] = {
              name: `${letr.toUpperCase()}`,
              value: letr.toLowerCase(),
            };
        });
        // fix order
        letrs = Object.entries(letrs)
          .sort()
          .reduce((o, [k, v]) => ((o[k] = v), o), {});
        return Object.values(letrs);
      },
      filterValue: (v) => v.first_name.charAt(0).toLowerCase(),
    },
    {
      key: "last_name",
      title: "LAST_NAME",
      value: (v) => v.last_name,
      sortable: true,
      filterOptions: (rows) => {
        // use first letter of last_name to generate filter
        let letrs = {};
        rows.forEach((row) => {
          let letr = row.last_name.charAt(0);
          if (letrs[letr] === undefined)
            letrs[letr] = {
              name: `${letr.toUpperCase()}`,
              value: letr.toLowerCase(),
            };
        });
        // fix order
        letrs = Object.entries(letrs)
          .sort()
          .reduce((o, [k, v]) => ((o[k] = v), o), {});
        return Object.values(letrs);
      },
      filterValue: (v) => v.last_name.charAt(0).toLowerCase(),
    },
    {
      key: "pet",
      title: "Pet",
      value: (v) => v.pet,
      renderValue: (v) => v.pet.charAt(0).toUpperCase() + v.pet.substring(1), // capitalize
      sortable: true,
      filterOptions: ["bird", "cat", "dog"], // provide array
    },
  ];

  const balances_cols = [
    { key: "name", title: "Name", value: (v) => v.name },
    { key: "balances", title: "Balance", value: (v) => v.balances_str },
  ];

  const transactions_cols = [
    { key: "datestr", title: "Date", value: (v) => v.datestr },
    { key: "amount", title: "Amount", value: (v) => v.amount },
    { key: "name", title: "Name", value: (v) => v.name },
    { key: "merchant_name", title: "Merchant", value: (v) => v.merchant_name },
    { key: "category", title: "Category_Detailed", value: (v) => v.category },
    {
      key: "personal_finance_category",
      title: "Category_Primary",
      value: (v) => v.personal_finance_category_primary,
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
        await fetch("http://127.0.0.1:8000/exchange_public_token/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ token: public_token }),
        });
        await refresh_and_update();
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

  onMount(async () => {
    // check existing accounts
    await check_existing_tokens();

    // refresh and update data
    await refresh_and_update();
  });
</script>

<svelte:head>
  <script
    src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
</svelte:head>

<main>
  <!-- <div class="horizontal"> -->

  <button id="link-button" on:click={link_account_btn}> Link Account </button>

  <div>
    <h1>Account Balances Overview</h1>
    <img
      src={balances_overview}
      class="balances_overview"
      alt="Balances Overview"
    />
    <SvelteTable columns={balances_cols} rows={$balances} />
  </div>

  <div>
    <h1>Transactions Overview</h1>
    <div class="arrange-horizontally">
      <div>
        <h3>Transactions Out</h3>
        <img
          src={transactions_out}
          class="transactions_out"
          alt="Transactions Out"
        />
      </div>
      <div>
        <h3>Transactions In</h3>
        <img
          src={transactions_in}
          class="transactions_in"
          alt="Transactions In"
        />
      </div>
    </div>
    <SvelteTable columns={transactions_cols} rows={$transactions} />
  </div>

  <SvelteTable {columns} {rows} />

  <div class="card">
    <Counter />
  </div>
</main>

<style>
  .balances_overview {
    height: 30em;
    will-change: filter;
  }
  .transactions_out {
    height: 20em;
    will-change: filter;
  }
  .transactions_in {
    height: 20em;
    will-change: filter;
  }
  .arrange-horizontally > * {
    display: inline-block;
    text-align: center;
  }
</style>
