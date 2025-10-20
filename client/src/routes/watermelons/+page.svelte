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
	};

	const API_URL = 'http://localhost:8001';
	let watermelons: Watermelon[] = [];

	let showDatePickerModal = false;
	let selectedDate = '';
	let imageDataUrl: string | null = null;

	// Helper to format date to YYYY-MM-DD for the date input
	function toISODateString(date: Date) {
		const year = date.getFullYear();
		const month = (date.getMonth() + 1).toString().padStart(2, '0');
		const day = date.getDate().toString().padStart(2, '0');
		return `${year}-${month}-${day}`;
	}

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
				createdAt: new Date(wm.createdAt)
			}));
		} catch (error) {
			console.error('Error fetching watermelons:', error);
		}
	});

	async function onFileSelected(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files[0]) {
			const file = target.files[0];

			// Pre-select date with file's last modified date
			selectedDate = toISODateString(new Date(file.lastModified));

			const reader = new FileReader();
			reader.onload = (e) => {
				if (typeof e.target?.result === 'string') {
					imageDataUrl = e.target.result;
					showDatePickerModal = true;
				}
			};
			reader.readAsDataURL(file);

			// Reset file input value to allow selecting the same file again
			target.value = '';
		}
	}

	function cancelUpload() {
		showDatePickerModal = false;
		imageDataUrl = null;
		selectedDate = '';
	}

	async function confirmUpload() {
		if (!imageDataUrl || !selectedDate) return;

		try {
			const response = await fetch(`${API_URL}/watermelons`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					image_base64: imageDataUrl,
					createdAt: new Date(selectedDate).toISOString()
				})
			});

			if (!response.ok) {
				throw new Error('Failed to upload watermelon');
			}

			const newWatermelonData = await response.json();
			const newWatermelon: Watermelon = {
				...newWatermelonData,
				src: `${API_URL}${newWatermelonData.src}`,
				createdAt: new Date(newWatermelonData.createdAt)
			};
			watermelons = [...watermelons, newWatermelon];
		} catch (error) {
			console.error('Error uploading watermelon:', error);
			alert('Failed to upload watermelon. See console for details.');
		} finally {
			cancelUpload();
		}
	}

	async function saveRatings(watermelon: Watermelon) {
		try {
			const response = await fetch(`${API_URL}/watermelons/${watermelon.id}`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					rachy: watermelon.rachy,
					davey: watermelon.davey
				})
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || 'Failed to save ratings');
			}

			alert('Ratings saved successfully!');
		} catch (error) {
			console.error('Error saving ratings:', error);
			alert(`Error: ${error}`);
		}
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
			on:change={onFileSelected}
			accept="image/*"
		/>
	</div>

	<!-- Date Picker Modal -->
	{#if showDatePickerModal}
		<div
			class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 p-4"
			on:click|self={cancelUpload}
		>
			<div class="bg-white p-6 rounded-lg shadow-xl w-full max-w-md">
				<h2 class="text-2xl font-bold mb-4 text-center">Confirm Memory Date</h2>
				{#if imageDataUrl}
					<img src={imageDataUrl} alt="Preview" class="w-full h-48 object-cover rounded-md mb-4" />
				{/if}

				<label for="memory-date" class="block text-sm font-medium text-gray-700 mb-1"
					>Date</label
				>
				<input
					type="date"
					id="memory-date"
					bind:value={selectedDate}
					class="w-full p-2 border border-gray-300 rounded-md mb-6"
				/>

				<div class="flex justify-end space-x-4">
					<button
						on:click={cancelUpload}
						class="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded-full"
					>
						Cancel
					</button>
					<button
						on:click={confirmUpload}
						class="bg-rose-500 hover:bg-rose-600 text-white font-bold py-2 px-4 rounded-full"
					>
						Upload
					</button>
				</div>
			</div>
		</div>
	{/if}

	{#if watermelons.length === 0}
		<div class="text-center py-20">
			<p class="text-gray-500 text-lg">Upload a photo to start tracking your watermelon memories!</p>
			<div class="text-6xl mt-4">🍉</div>
		</div>
	{/if}

	<div class="space-y-6 p-2">
		{#each watermelons.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime()) as watermelon (watermelon.id)}
			<div class="bg-white p-4 shadow-md rounded-lg w-full border border-rose-100">
				<div class="flex flex-col lg:flex-row gap-4 items-center">
					<div class="w-full lg:w-1/4">
						<img
							src={watermelon.src}
							alt="A watermelon"
							class="w-full h-48 object-cover rounded-md border-2 border-rose-100"
						/>
						<p class="text-center text-gray-500 mt-1 text-sm">
							{watermelon.createdAt.toLocaleDateString('en-US', {
								year: 'numeric',
								month: 'long',
								day: 'numeric'
							})}
						</p>
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
				<div class="mt-6 text-right">
					<button
						on:click={() => saveRatings(watermelon)}
						class="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-full shadow-lg transition-transform transform hover:scale-105"
					>
						Save Ratings
					</button>
				</div>
			</div>
		{/each}
	</div>
</div>
