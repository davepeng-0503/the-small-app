<script lang="ts">
	import { page } from "$app/stores";

	let { children } = $props();
</script>

<div class="flex h-screen bg-gray-50">
	<aside class="w-64 bg-white shadow-lg flex flex-col flex-shrink-0">
		<div class="p-5 border-b text-center">
			<a
				href="/"
				class="text-3xl text-green-700 hover:text-green-800"
				style="font-family: 'Comic Sans MS', cursive, sans-serif;"
			>
				My Scrapbook
			</a>
		</div>
		<nav class="p-4">
			<ul>
				<li>
					<a
						href="/watermelons"
						class="block py-2 px-4 rounded-md text-lg text-gray-700 hover:bg-red-100 hover:text-red-700 transition-colors"
						class:font-bold={$page.url.pathname.startsWith("/watermelons")}
						class:text-red-600={$page.url.pathname.startsWith("/watermelons")}
						class:bg-red-100={$page.url.pathname.startsWith("/watermelons")}
					>
						🍉 Watermelons
					</a>
				</li>
			</ul>
		</nav>
	</aside>

	<main class="flex-1 overflow-y-auto">
		{@render children?.()}
	</main>
</div>
