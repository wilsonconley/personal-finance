<script>
  // component props
  export let handleClick;

  let condition = "";
  let categorize = "";
</script>

<main>
  <div class="card">
    <div class="left-side">
      <label for="rule_condition">if </label>
      <input bind:value={condition} id="rule_condition" name="rule_condition" />
      <label for="rule_categorize">, categorize as </label>
      <input
        bind:value={categorize}
        id="rule_categorize"
        name="rule_categorize"
      />
    </div>
    <button on:click={() => handleClick(condition, categorize)}>Add</button>
  </div>
</main>

<style>
  .card {
    margin: auto;
    width: 700px;
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
    width: 575px;
  }
</style>
