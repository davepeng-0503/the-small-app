<script lang="ts">
	import { onMount } from 'svelte';

	type Ratings = {
		texture: number;
		juiciness: number;
		sweetness: number;
	};

	type Watermelon = {
		id: string;
		src: string;
		createdAt: Date;
		rachy: Ratings;
		davey: Ratings;
		editing: boolean;
	};

	const API_URL = 'http://localhost:8001';
	let watermelons: Watermelon[] = [];

	onMount(async () => {
		try {
			const response = await fetch(`${API_URL}/watermelons`);
			if (!response.ok) {
				throw new Error('Failed to fetch watermelons');
			}
			const data = await response.json();
			watermelons = data.map((wm: any) => ({
				...wm,
				src: `${API_URL}${wm.src}`,
				createdAt: new Date(wm.createdAt),
				editing: false
			}));
		} catch (error) {
			console.error('Error fetching watermelons:', error);
		}
	});

	async function handleFileUpload(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files[0]) {
			const file = target.files[0];
			const reader = new FileReader();
			reader.onload = async (e) => {
				if (typeof e.target?.result === 'string') {
					try {
						const response = await fetch(`${API_URL}/watermelons`, {
							method: 'POST',
							headers: {
								'Content-Type': 'application/json'
							},
							body: JSON.stringify({ image_base64: e.target.result })
						});

						if (!response.ok) {
							throw new Error('Failed to upload watermelon');
						}

						const newWatermelonData = await response.json();
						const newWatermelon: Watermelon = {
							...newWatermelonData,
							src: `${API_URL}${newWatermelonData.src}`,
							createdAt: new Date(newWatermelonData.createdAt),
							editing: true
						};
						watermelons = [...watermelons, newWatermelon];
					} catch (error) {
						console.error('Error uploading watermelon:', error);
						alert('Failed to upload watermelon. See console for details.');
					}
				}
			};
			reader.readAsDataURL(file);
		}
	}

	function toggleEdit(id: string) {
		watermelons = watermelons.map((wm) =>
			wm.id === id ? { ...wm, editing: !wm.editing } : wm
		);
	}

	async function saveChanges(watermelon: Watermelon) {
		try {
			const response = await fetch(`${API_URL}/watermelons/${watermelon.id}`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					rachy: watermelon.rachy,
					davey: watermelon.davey,
					createdAt: watermelon.createdAt.toISOString()
				})
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || 'Failed to save ratings');
			}

			toggleEdit(watermelon.id);
		} catch (error) {
			console.error('Error saving ratings:', error);
			alert(`Error: ${error}`);
		}
	}

	function formatDateForInput(date: Date): string {
		const d = new Date(date);
		const year = d.getFullYear();
		let month = '' + (d.getMonth() + 1);
		let day = '' + d.getDate();

		if (month.length < 2) month = '0' + month;
		if (day.length < 2) day = '0' + day;

		return [year, month, day].join('-');
	}

	function handleDateChange(event: Event, watermelonId: string) {
		const target = event.target as HTMLInputElement;
		const [year, month, day] = target.value.split('-').map(Number);

		watermelons = watermelons.map((wm) => {
			if (wm.id === watermelonId) {
				return { ...wm, createdAt: new Date(year, month - 1, day) };
			}
			return wm;
		});
	}
</script>

<div class="p-6 min-h-full">
	<h1 class="text-4xl text-rose-500 font-bold mb-8 text-center">Our Watermelon Memories</h1>

	<div class="mb-8 text-center">
		<label
			for="file-upload"
			class="cursor-pointer bg-rose-400 hover:bg-rose-500 text-white font-bold py-2 px-4 rounded-full shadow-lg transition-transform transform hover:scale-105"
		>
			+ Add a Watermelon Memory
		</label>
		<input
			id="file-upload"
			type="file"
			class="hidden"
			on:change={handleFileUpload}
			accept="image/*"
		/>
	</div>

	{#if watermelons.length === 0}
		<div class="text-center py-20">
			<p class="text-gray-500 text-lg">Upload a photo to start tracking your watermelon memories!</p>
			<div class="text-6xl mt-4">🍉</div>
		</div>
	{/if}

	<div class="space-y-6 p-2">
		{#each watermelons.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime()) as watermelon (watermelon.id)}
			<div class="bg-white p-4 pt-12 shadow-md rounded-lg w-full border border-rose-100 relative">
				<div class="absolute top-2 left-2 z-10">
					{#if watermelon.editing}
						<button
							on:click={() => saveChanges(watermelon)}
							class="bg-rose-400 hover:bg-rose-500 text-white font-bold py-2 px-4 rounded-full shadow-lg transition-transform transform hover:scale-105"
						>
							Save
						</button>
					{:else}
						<button
							on:click={() => toggleEdit(watermelon.id)}
							class="text-gray-400 hover:text-gray-600 p-2 rounded-full"
							aria-label="Edit watermelon"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-6 w-6"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"
								/>
							</svg>
						</button>
					{/if}
				</div>

				<div class="flex flex-col lg:flex-row gap-4 items-center">
					<div class="w-full lg:w-1/4">
						<img
							src={watermelon.src}
							alt="A watermelon"
							class="w-full h-48 object-cover rounded-md border-2 border-rose-100"
						/>
						{#if watermelon.editing}
							<input
								type="date"
								class="mt-1 w-full text-center border-gray-300 rounded-md shadow-sm focus:border-rose-300 focus:ring focus:ring-rose-200 focus:ring-opacity-50 text-sm p-1"
								value={formatDateForInput(watermelon.createdAt)}
								on:change={(e) => handleDateChange(e, watermelon.id)}
							/>
						{:else}
							<p class="text-center text-gray-500 mt-1 text-sm">
								{watermelon.createdAt.toLocaleDateString('en-US', {
									year: 'numeric',
									month: 'long',
									day: 'numeric'
								})}
							</p>
						{/if}
					</div>
					<div class="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
						<div>
							<h3 class="text-xl font-bold text-pink-400 mb-2 text-center">Rachy's Rating</h3>
							<div class="mb-2">
								<label
									for="rachy-texture-{watermelon.id}"
									class="block text-sm font-medium text-gray-700">Texture</label
								>
								<input
									type="range"
									id="rachy-texture-{watermelon.id}"
									bind:value={watermelon.rachy.texture}
									min="1"
									max="100"
									class="w-full h-2 bg-rose-100 rounded-lg appearance-none cursor-pointer"
									disabled={!watermelon.editing}
								/>
							</div>
							<div class="mb-2">
								<label
									for="rachy-juiciness-{watermelon.id}"
									class="block text-sm font-medium text-gray-700">Juiciness</label
								>
								<input
									type="range"
									id="rachy-juiciness-{watermelon.id}"
									bind:value={watermelon.rachy.juiciness}
									min="1"
									max="100"
									class="w-full h-2 bg-rose-100 rounded-lg appearance-none cursor-pointer"
									disabled={!watermelon.editing}
								/>
							</div>
							<div>
								<label
									for="rachy-sweetness-{watermelon.id}"
									class="block text-sm font-medium text-gray-700">Sweetness</label
								>
								<input
									type="range"
									id="rachy-sweetness-{watermelon.id}"
									bind:value={watermelon.rachy.sweetness}
									min="1"
									max="100"
									class="w-full h-2 bg-rose-100 rounded-lg appearance-none cursor-pointer"
									disabled={!watermelon.editing}
								/>
							</div>
							<div class="mt-4 text-center">
								<div class="text-5xl font-bold text-pink-400">
									{Math.round(
										(watermelon.rachy.texture +
											watermelon.rachy.juiciness +
											watermelon.rachy.sweetness) /
											3
									)}
								</div>
							</div>
						</div>
						<div>
							<h3 class="text-xl font-bold text-sky-400 mb-2 text-center">Davey's Rating</h3>
							<div class="mb-2">
								<label
									for="davey-texture-{watermelon.id}"
									class="block text-sm font-medium text-gray-700">Texture</label
								>
								<input
									type="range"
									id="davey-texture-{watermelon.id}"
									bind:value={watermelon.davey.texture}
									min="1"
									max="100"
									class="w-full h-2 bg-rose-100 rounded-lg appearance-none cursor-pointer"
									disabled={!watermelon.editing}
								/>
							</div>
							<div class="mb-2">
								<label
									for="davey-juiciness-{watermelon.id}"
									class="block text-sm font-medium text-gray-700">Juiciness</label
								>
								<input
									type="range"
									id="davey-juiciness-{watermelon.id}"
									bind:value={watermelon.davey.juiciness}
									min="1"
									max="100"
									class="w-full h-2 bg-rose-100 rounded-lg appearance-none cursor-pointer"
									disabled={!watermelon.editing}
								/>
							</div>
							<div>
								<label
									for="davey-sweetness-{watermelon.id}"
									class="block text-sm font-medium text-gray-700">Sweetness</label
								>
								<input
									type="range"
									id="davey-sweetness-{watermelon.id}"
									bind:value={watermelon.davey.sweetness}
									min="1"
									max="100"
									class="w-full h-2 bg-rose-100 rounded-lg appearance-none cursor-pointer"
									disabled={!watermelon.editing}
								/>
							</div>
							<div class="mt-4 text-center">
								<div class="text-5xl font-bold text-sky-400">
									{Math.round(
										(watermelon.davey.texture +
											watermelon.davey.juiciness +
											watermelon.davey.sweetness) /
											3
									)}
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		{/each}
	</div>
</div>
