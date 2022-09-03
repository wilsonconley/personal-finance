<script>
  import balances from "./assets/balances.svg";
  import Counter from "./lib/Counter.svelte";
  // import htmlContent from "./assets/balances.html";
  // import "./assets/balances.html";

  async function readFile() {
    let scripts = document.getElementsByTagName("script"),
      src = scripts[scripts.length - 1].src;
    // src[0:4];
    const response = await fetch("file://./assets/balances.html").then(
      (response) => response.text()
    );
    console.log(response);
    return response;
    // .then((text) => (document.getElementById("homePage").innerHTML = text));
  }
  let balancesHtml = "";
  readFile().then((data) => (balancesHtml = data));
</script>

<main>
  <!-- <div>
    <img src={balances} class="logo svelte" alt="Svelte Logo" />
  </div> -->

  <div id="homePage">
    {@html balancesHtml}
  </div>

  <div class="card">
    <Counter />
  </div>
</main>

<style>
  /* .logo {
    height: 25em;
    padding: 1.5em;
    will-change: filter;
  } */
</style>
