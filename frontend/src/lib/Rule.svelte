<script>
  // component props
  export let handleClick;
  export let search_str, transaction_field, categorize;
</script>

<main>
  <div class="card">
    <div class="left-side">
      <p>
        if <span class="condition">{search_str}</span> in
        <span class="condition">{transaction_field}</span>, categorize as
        <span class="condition">{categorize}</span>
      </p>
    </div>
    <button on:click={handleClick}>Remove</button>
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
  }

  .card > * {
    display: inline-block;
    text-align: center;
  }

  .condition {
    background: #777777;
    border-radius: 5px;
    padding: 0 5px 0 5px;
    font-style: italic;
  }

  .left-side {
    width: 775px;
  }
</style>
