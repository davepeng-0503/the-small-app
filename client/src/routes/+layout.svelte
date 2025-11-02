<script lang="ts">
	import { page } from "$app/stores";
	import "../app.css";

	let { children } = $props();
</script>

<div class="flex h-screen bg-rose-50 font-sans">
	<aside class="w-64 bg-white border-r border-rose-200 flex flex-col flex-shrink-0">
		<div class="p-5 border-b border-rose-200 text-center">
			<a href="/" class="text-3xl text-rose-500 hover:text-rose-600 font-bold">
				R&D
			</a>
		</div>
		<nav class="p-4">
			<ul>
				<li>
					<a
						href="/watermelons"
						class="block py-2 px-4 rounded-md text-lg text-gray-700 hover:bg-rose-100 hover:text-rose-500 transition-colors"
						class:font-bold={$page.url.pathname.startsWith("/watermelons")}
						class:text-rose-500={$page.url.pathname.startsWith("/watermelons")}
						class:bg-rose-100={$page.url.pathname.startsWith("/watermelons")}
					>
						🍉 Watermelons
					</a>
				</li>
				<li>
					<a
						href="/polaroids"
						class="block py-2 px-4 rounded-md text-lg text-gray-700 hover:bg-rose-100 hover:text-rose-500 transition-colors"
						class:font-bold={$page.url.pathname.startsWith("/polaroids")}
						class:text-rose-500={$page.url.pathname.startsWith("/polaroids")}
						class:bg-rose-100={$page.url.pathname.startsWith("/polaroids")}
					>
						📸 Polaroids
					</a>
				</li>
				<li>
					<a
						href="/timeline"
						class="block py-2 px-4 rounded-md text-lg text-gray-700 hover:bg-rose-100 hover:text-rose-500 transition-colors"
						class:font-bold={$page.url.pathname.startsWith("/timeline")}
						class:text-rose-500={$page.url.pathname.startsWith("/timeline")}
						class:bg-rose-100={$page.url.pathname.startsWith("/timeline")}
					>
						⏳ Timeline
					</a>
				</li>
			</ul>
		</nav>
	</aside>

	<main class="flex-1 overflow-y-auto">
		{@render children?.()}
	</main>
</div>
