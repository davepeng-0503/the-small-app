<script lang="ts">
	let { children } = $props();
</script>

<div class="app-container">
	<aside class="sidebar">
		<!-- Future navigation links will be placed here -->
	</aside>

	<main class="main-content">
		{@render children?.()}
	</main>
</div>

<style>
	.app-container {
		display: flex;
		height: 100vh;
	}

	.sidebar {
		width: 250px;
		background-color: #f4f4f4;
		border-right: 1px solid #ddd;
		padding: 1rem;
	}

	.main-content {
		flex: 1;
		padding: 1rem;
		overflow-y: auto;
	}

	:global(body) {
		margin: 0;
		padding: 0;
		box-sizing: border-box;
		font-family: sans-serif;
	}
</style>
