<script>
  // component props
  export let handleClick;

  let search_str = "";
  let transaction_field = "name";
  let categorize = "";

  let fields = [
    "name",
    "pending_transaction_id",
    "category_id",
    "category",
    "location",
    "payment_meta",
    "account_owner",
    "account_id",
    "amount",
    "iso_currency_code",
    "unofficial_currency_code",
    "date",
    "pending",
    "transaction_id",
    "payment_channel",
    "authorized_date",
    "authorized_datetime",
    "datetime",
    "transaction_code",
    "check_number",
    "merchant_name",
    "personal_finance_category",
    "transaction_type",
    "datestr",
    "personal_finance_category_primary",
  ];
</script>

<main>
  <div class="card">
    <div class="left-side">
      <label for="search_str">if </label>
      <input bind:value={search_str} id="search_str" name="search_str" />
      <label for="transaction_field"> in </label>
      <select
        bind:value={transaction_field}
        id="transaction_field"
        name="transaction_field"
      >
        {#each fields as field}
          <option value={field}>
            {field}
          </option>
        {/each}
      </select>
      <label for="rule_categorize">, categorize as </label>
      <input
        bind:value={categorize}
        id="rule_categorize"
        name="rule_categorize"
      />
    </div>
    <button
      on:click={() => handleClick(search_str, transaction_field, categorize)}
      >Add</button
    >
  </div>
</main>

<style>
  .card {
    margin: auto;
    width: 1000px;
    height: 56px;
    border-radius: 5px;
    background: #bebebe33;
    padding: 0 0 0 0;
    line-height: 56px;
  }

  .card > * {
    display: inline-block;
    text-align: center;
  }

  .left-side {
    width: 875px;
  }
</style>
