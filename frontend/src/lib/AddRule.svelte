<script>
  // component props
  export let handleClick;

  let search_str = "";
  let transaction_field = "";
  let categorize = "";
</script>

<main>
  <div class="card">
    <div class="left-side">
      <label for="search_str">if </label>
      <input bind:value={search_str} id="search_str" name="search_str" />
      <label for="transaction_field"> in </label>
      <input
        bind:value={transaction_field}
        id="transaction_field"
        name="transaction_field"
      />
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
    width: 900px;
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
    width: 775px;
  }
</style>
