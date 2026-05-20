/**
 * ECharts 按需引入配置
 * 仅导入需要的图表类型和组件，减少打包体积
 */
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart, LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent
} from 'echarts/components'

// 注册必要的渲染器和图表类型
use([
  CanvasRenderer,
  PieChart,
  BarChart,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent
])

// 导出 ECharts 核心，供 vue-echarts 使用
export { use }
