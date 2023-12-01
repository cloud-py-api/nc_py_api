<template>
	<NcContent app-name="ui_example">
		<NcAppNavigation>
			<template #list>
				<NcAppNavigationItem id="app-index"
					:to="{ name: 'ui_example_index' }"
					:name="t('ui_example', 'Home')"
					:exact="true">
					<template #icon>
						<Home :size="20" />
					</template>
				</NcAppNavigationItem>
				<NcAppNavigationItem id="app-file-picker"
					:to="{ name: 'ui_example_file_picker' }"
					:name="t('ui_example', 'Files')">
					<template #icon>
						<Folder :size="20" />
					</template>
				</NcAppNavigationItem>
			</template>
		</NcAppNavigation>
		<NcAppContent>
			<router-view />
		</NcAppContent>
	</NcContent>
</template>

<script>
import NcContent from '@nextcloud/vue/dist/Components/NcContent.js'
import NcAppContent from '@nextcloud/vue/dist/Components/NcAppContent.js'
import NcAppNavigation from '@nextcloud/vue/dist/Components/NcAppNavigation.js'
import NcAppNavigationItem from '@nextcloud/vue/dist/Components/NcAppNavigationItem.js'
import Home from 'vue-material-design-icons/Home.vue'
import Folder from 'vue-material-design-icons/Folder.vue'

export default {
	name: 'App',
	components: {
		NcContent,
		NcAppContent,
		NcAppNavigation,
		NcAppNavigationItem,
		Home,
		Folder,
	},
}
</script>
