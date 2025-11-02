<script lang="ts">
	import { onMount } from 'svelte';
	import type { Polaroid } from '../app';

	type PositionedPolaroid = Polaroid & {
		x: number;
		y: number;
		rotation: number;
	};

	const API_URL = 'http://localhost:9999';
	let polaroids: PositionedPolaroid[] = [];

	onMount(async () => {
		try {
			const response = await fetch(`${API_URL}/polaroids`);
			if (!response.ok) throw new Error('Failed to fetch polaroids');

			const data = await response.json();
			let fetchedPolaroids: Polaroid[] = data.map((p: any) => ({
				...p,
				src: p.src,
				createdAt: new Date(p.createdAt),
				diaryEntry: p.diary_entry || '',
				stickers: p.stickers || []
			}));

			// Shuffle the polaroids array for random order and z-indexing
			for (let i = fetchedPolaroids.length - 1; i > 0; i--) {
				const j = Math.floor(Math.random() * (i + 1));
				[fetchedPolaroids[i], fetchedPolaroids[j]] = [fetchedPolaroids[j], fetchedPolaroids[i]];
			}

			polaroids = fetchedPolaroids.map((p) => ({
				...p,
				// Using values that will hopefully keep polaroids mostly in view
				x: Math.random() * 75, // left: 0% to 75% to keep it mostly on screen
				y: Math.random() * 70, // top: 0% to 70%
				rotation: Math.random() * 50 - 25 // rotation: -25deg to 25deg
			}));
		} catch (error) {
			console.error('Error fetching polaroids:', error);
		}
	});
</script>

<svelte:head>
	<title>Rachy & Davey</title>
</svelte:head>

<div class="relative w-screen h-screen overflow-hidden bg-rose-50 font-sans">
	<h1
		class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-7xl sm:text-8xl md:text-9xl font-bold text-rose-200 z-0 select-none"
	>
		Rachy & Davey
	</h1>

	<div class="absolute top-0 left-0 w-full h-full">
		{#each polaroids as polaroid, i (polaroid.id)}
			<div
				class="polaroid-container absolute bg-white p-2 sm:p-3 md:p-4 shadow-xl transition-transform duration-300 hover:scale-110 hover:z-50 cursor-pointer"
				style="top: {polaroid.y}%; left: {polaroid.x}%; transform: rotate({polaroid.rotation}deg); z-index: {i +
					1};"
			>
				<img
					src={polaroid.src}
					alt={polaroid.description || 'A photo from Rachy & Davey'}
					class="w-full h-auto aspect-square object-cover bg-gray-100"
				/>
				{#if polaroid.description}
					<p class="mt-2 text-center text-xs md:text-sm italic text-gray-700">
						{polaroid.description}
					</p>
				{/if}
			</div>
		{/each}
	</div>
</div>

<style lang="postcss">
	.polaroid-container {
		width: 25vw;
		max-width: 220px;
		min-width: 120px;
	}

	@import url('https://fonts.googleapis.com/css2?family=Kalam:wght@700&display=swap');
	h1 {
		font-family: 'Kalam', cursive;
	}
</style>
