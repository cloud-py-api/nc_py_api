<template>
	<div class="test-files-pickers">
		<h2>{{ t('ui_example', 'Test file pickers') }}</h2>
		<p>
			<b>{{ t('ui_example', 'Selected file from Nextcloud: ') }}</b>
			{{ selectedFile }}
		</p>
		<p><b>{{ t('ui_example', 'File info: ') }}</b>{{ selectedFileInfo }}</p>
		<p><b>{{ t('ui_example', 'File size: ') }}</b>{{ formattedSize }}</p>
		<NcButton @click="selectTestFile">
			{{ t('ui_example', 'Select test file') }}
		</NcButton>
		<NcButton @click="sendToExApp">
			{{ t('ui_example', 'Send test file to ExApp') }}
		</NcButton>
	</div>
</template>

<script>
import NcButton from '@nextcloud/vue/dist/Components/NcButton.js'
import { getFilePickerBuilder } from '@nextcloud/dialogs'
import { formatBytes, requestFileInfo } from '../files.js'

export default {
	name: 'FilePicker',
	components: {
		NcButton,
	},
	data() {
		return {
			selectedFile: '',
			selectedFileInfo: {},
		}
	},
	computed: {
		formattedSize() {
			return formatBytes(this.selectedFileInfo?.size || 0) || ''
		},
	},
	methods: {
		getFilesPicker(title) {
			return getFilePickerBuilder(title)
				.setMultiSelect(false)
				.setType(1)
				.allowDirectories(true)
				.build()
		},
		selectTestFile() {
			this.getFilesPicker(t('ui_example', 'Select test file')).pick().then(filePath => {
				this.selectedFile = filePath
				requestFileInfo(filePath).then(fileInfo => {
					this.selectedFileInfo = fileInfo
				})
			})
		},
		sendToExApp() {
			this.$store.dispatch('sendNextcloudFileToExApp', this.selectedFileInfo)
		},
	},
}
</script>

<style lang="scss" scoped>
.test-files-pickers {
	width: 100%;
	max-width: 600px;
	display: flex;
	flex-direction: column;
	align-items: center;
	margin: 30px auto;
	padding: 20px;

	p, button {
		margin: 10px 0;
	}
}
</style>
