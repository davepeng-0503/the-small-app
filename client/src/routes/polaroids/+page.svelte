<script lang="ts">
	import { onMount } from 'svelte';

	type Polaroid = {
		id: string;
		src: string;
		createdAt: Date;
		description: string;
		editing: boolean;
	};

	const API_URL = 'http://localhost:8001';
	let polaroids: Polaroid[] = [];

	onMount(async () => {
		try {
			const response = await fetch(`${API_URL}/polaroids`);
			if (!response.ok) {
				throw new Error('Failed to fetch polaroids');
			}
			const data = await response.json();
			polaroids = data.map((p: any) => ({
				...p,
				src: `${API_URL}${p.src}`,
				createdAt: new Date(p.createdAt),
				editing: false
			}));
		} catch (error) {
			console.error('Error fetching polaroids:', error);
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
						const response = await fetch(`${API_URL}/polaroids`, {
							method: 'POST',
							headers: {
								'Content-Type': 'application/json'
							},
							body: JSON.stringify({ image_base64: e.target.result })
						});

						if (!response.ok) {
							throw new Error('Failed to upload polaroid');
						}

						const newPolaroidData = await response.json();
						const newPolaroid: Polaroid = {
							...newPolaroidData,
							src: `${API_URL}${newPolaroidData.src}`,
							createdAt: new Date(newPolaroidData.createdAt),
							editing: true // Start in editing mode
						};
						polaroids = [...polaroids, newPolaroid];
					} catch (error) {
						console.error('Error uploading polaroid:', error);
						alert('Failed to upload polaroid. See console for details.');
					}
				}
			};
			reader.readAsDataURL(file);
		}
	}

	function toggleEdit(id: string) {
		polaroids = polaroids.map((p) => (p.id === id ? { ...p, editing: !p.editing } : p));
	}

	async function saveChanges(polaroid: Polaroid) {
		try {
			const response = await fetch(`${API_URL}/polaroids/${polaroid.id}`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					description: polaroid.description,
					createdAt: polaroid.createdAt.toISOString()
				})
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || 'Failed to save polaroid');
			}

			toggleEdit(polaroid.id);
		} catch (error) {
			console.error('Error saving polaroid:', error);
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

	function handleDateChange(event: Event, polaroidId: string) {
		const target = event.target as HTMLInputElement;
		const [year, month, day] = target.value.split('-').map(Number);

		polaroids = polaroids.map((p) => {
			if (p.id === polaroidId) {
				return { ...p, createdAt: new Date(year, month - 1, day) };
			}
			return p;
		});
	}
</script>

<div class="p-6 min-h-full">
	<h1 class="text-4xl text-rose-500 font-bold mb-8 text-center">Polaroid Memories</h1>

	<div class="mb-8 text-center">
		<label
			for="file-upload"
			class="cursor-pointer bg-rose-400 hover:bg-rose-500 text-white font-bold py-2 px-4 rounded-full shadow-lg transition-transform transform hover:scale-105"
		>
			+ Add a Polaroid
		</label>
		<input
			id="file-upload"
			type="file"
			class="hidden"
			on:change={handleFileUpload}
			accept="image/*"
		/>
	</div>

	{#if polaroids.length === 0}
		<div class="text-center py-20">
			<p class="text-gray-500 text-lg">Upload a photo to start creating your polaroid wall!</p>
			<div class="text-6xl mt-4">📸</div>
		</div>
	{/if}

	<div
		class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6 p-4"
	>
		{#each polaroids.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime()) as polaroid (polaroid.id)}
			<div
				class="bg-white p-4 pb-12 shadow-lg rounded-sm flex flex-col relative group transform hover:-translate-y-2 transition-transform duration-300"
			>
				<div
					class="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2"
				>
					{#if polaroid.editing}
						<button
							on:click={() => saveChanges(polaroid)}
							class="bg-rose-400 hover:bg-rose-500 text-white font-bold py-1 px-3 rounded-full shadow-lg text-sm"
						>
							Save
						</button>
					{:else}
						<button
							on:click={() => toggleEdit(polaroid.id)}
							class="bg-white/80 text-gray-600 hover:text-gray-900 p-2 rounded-full shadow-md"
							aria-label="Edit polaroid"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-4 w-4"
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

				<div class="bg-gray-800 border-2 border-gray-100">
					<img src={polaroid.src} alt="A polaroid" class="w-full h-auto aspect-square object-cover" />
				</div>

				<div class="w-full text-center absolute bottom-2 left-0 right-0 px-4">
					{#if polaroid.editing}
						<textarea
							bind:value={polaroid.description}
							placeholder="Add a description..."
							class="text-center w-full border-gray-300 rounded-md shadow-sm focus:border-rose-300 focus:ring focus:ring-rose-200 focus:ring-opacity-50 text-sm p-1 resize-none bg-rose-200"
						></textarea>
						<input
							type="date"
							class="mt-1 w-full text-center border-gray-300 rounded-md shadow-sm focus:border-rose-300 focus:ring focus:ring-rose-200 focus:ring-opacity-50 text-xs p-1"
							value={formatDateForInput(polaroid.createdAt)}
							on:change={(e) => handleDateChange(e, polaroid.id)}
						/>
					{:else}
						<p class="text-center text-gray-700 font-serif italic text-sm truncate h-5">
							{polaroid.description || ''}
						</p>
						<p class="text-center text-gray-500 mt-1 text-xs">
							{polaroid.createdAt.toLocaleDateString('en-US', {
								year: 'numeric',
								month: 'long',
								day: 'numeric'
							})}
						</p>
					{/if}
				</div>
			</div>
		{/each}
	</div>
</div>
