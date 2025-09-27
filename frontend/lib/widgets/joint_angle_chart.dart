import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:gait_analysis_app/models/gait_analysis_models.dart';
import 'package:gait_analysis_app/utils/constants.dart';
import 'package:gait_analysis_app/utils/app_theme.dart';

class JointAngleChart extends StatefulWidget {
  final JointAngles jointAngles;
  final double? height;

  const JointAngleChart({
    Key? key,
    required this.jointAngles,
    this.height = 300,
  }) : super(key: key);

  @override
  _JointAngleChartState createState() => _JointAngleChartState();
}

class _JointAngleChartState extends State<JointAngleChart>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  int _selectedJoint = 0;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.show_chart, color: AppColors.primary),
                const SizedBox(width: 8),
                const Text(
                  '関節角度波形',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                _buildJointSelector(),
              ],
            ),
            
            const SizedBox(height: 16),
            
            // 関節角度チャート
            SizedBox(
              height: widget.height,
              child: _buildAngleChart(),
            ),
            
            const SizedBox(height: 16),
            
            // 統計情報
            _buildAngleStatistics(),
          ],
        ),
      ),
    );
  }

  Widget _buildJointSelector() {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          _buildJointButton('股関節', 0, Icons.accessibility_new),
          _buildJointButton('膝関節', 1, Icons.sports_gymnastics),
          _buildJointButton('足関節', 2, Icons.directions_walk),
        ],
      ),
    );
  }

  Widget _buildJointButton(String label, int index, IconData icon) {
    final isSelected = _selectedJoint == index;
    
    return GestureDetector(
      onTap: () => setState(() => _selectedJoint = index),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(6),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 16,
              color: isSelected ? Colors.white : AppColors.textSecondary,
            ),
            const SizedBox(width: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                color: isSelected ? Colors.white : AppColors.textSecondary,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAngleChart() {
    List<double> angleData;
    String title;
    Color lineColor;

    switch (_selectedJoint) {
      case 0: // 股関節
        angleData = widget.jointAngles.hipFlexionDeg ?? [];
        title = '股関節屈曲角度';
        lineColor = AppColors.primary;
        break;
      case 1: // 膝関節
        angleData = widget.jointAngles.kneeFlexionDeg ?? [];
        title = '膝関節屈曲角度';
        lineColor = AppColors.accent;
        break;
      case 2: // 足関節
        angleData = widget.jointAngles.ankleDorsiflexionDeg ?? [];
        title = '足関節背屈角度';
        lineColor = AppColors.warning;
        break;
      default:
        angleData = [];
        title = '';
        lineColor = AppColors.primary;
    }

    if (angleData.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.warning_amber,
              color: AppColors.warning,
              size: 48,
            ),
            const SizedBox(height: 16),
            const Text(
              '関節角度データがありません',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 16,
              ),
            ),
          ],
        ),
      );
    }

    final spots = angleData.asMap().entries.map((entry) {
      return FlSpot(entry.key.toDouble(), entry.value);
    }).toList();

    return LineChart(
      LineChartData(
        gridData: FlGridData(
          show: true,
          drawVerticalLine: true,
          horizontalInterval: 10,
          verticalInterval: angleData.length / 6,
          getDrawingHorizontalLine: (value) {
            return FlLine(
              color: AppColors.textSecondary.withOpacity(0.2),
              strokeWidth: 1,
            );
          },
          getDrawingVerticalLine: (value) {
            return FlLine(
              color: AppColors.textSecondary.withOpacity(0.2),
              strokeWidth: 1,
            );
          },
        ),
        titlesData: FlTitlesData(
          show: true,
          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: AxisTitles(
            axisNameWidget: const Text(
              '時間 (フレーム)',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 12,
              ),
            ),
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 30,
              interval: angleData.length / 6,
              getTitlesWidget: (value, meta) {
                return Text(
                  value.toInt().toString(),
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 10,
                  ),
                );
              },
            ),
          ),
          leftTitles: AxisTitles(
            axisNameWidget: Text(
              '角度 (°)',
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 12,
              ),
            ),
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 40,
              getTitlesWidget: (value, meta) {
                return Text(
                  '${value.toInt()}°',
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 10,
                  ),
                );
              },
            ),
          ),
        ),
        borderData: FlBorderData(
          show: true,
          border: Border.all(
            color: AppColors.textSecondary.withOpacity(0.3),
            width: 1,
          ),
        ),
        minX: 0,
        maxX: (angleData.length - 1).toDouble(),
        minY: angleData.reduce((a, b) => a < b ? a : b) - 5,
        maxY: angleData.reduce((a, b) => a > b ? a : b) + 5,
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: lineColor,
            barWidth: 3,
            isStrokeCapRound: true,
            dotData: FlDotData(show: false),
            belowBarData: BarAreaData(
              show: true,
              color: lineColor.withOpacity(0.1),
            ),
          ),
        ],
        lineTouchData: LineTouchData(
          enabled: true,
          touchTooltipData: LineTouchTooltipData(
            tooltipBgColor: AppColors.surface,
            tooltipRoundedRadius: 8,
            getTooltipItems: (touchedSpots) {
              return touchedSpots.map((LineBarSpot touchedSpot) {
                return LineTooltipItem(
                  '${touchedSpot.y.toStringAsFixed(1)}°',
                  const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                );
              }).toList();
            },
          ),
        ),
      ),
    );
  }

  Widget _buildAngleStatistics() {
    List<double> angleData;
    String unit = '°';

    switch (_selectedJoint) {
      case 0:
        angleData = widget.jointAngles.hipFlexionDeg ?? [];
        break;
      case 1:
        angleData = widget.jointAngles.kneeFlexionDeg ?? [];
        break;
      case 2:
        angleData = widget.jointAngles.ankleDorsiflexionDeg ?? [];
        break;
      default:
        angleData = [];
    }

    if (angleData.isEmpty) {
      return const SizedBox.shrink();
    }

    final max = angleData.reduce((a, b) => a > b ? a : b);
    final min = angleData.reduce((a, b) => a < b ? a : b);
    final avg = angleData.reduce((a, b) => a + b) / angleData.length;
    final range = max - min;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStatItem('最大', max.toStringAsFixed(1), unit, AppColors.success),
          _buildStatItem('最小', min.toStringAsFixed(1), unit, AppColors.error),
          _buildStatItem('平均', avg.toStringAsFixed(1), unit, AppColors.primary),
          _buildStatItem('可動域', range.toStringAsFixed(1), unit, AppColors.warning),
        ],
      ),
    );
  }

  Widget _buildStatItem(String label, String value, String unit, Color color) {
    return Column(
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 10,
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: 4),
        Row(
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              value,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            Text(
              unit,
              style: TextStyle(
                fontSize: 12,
                color: color.withOpacity(0.7),
              ),
            ),
          ],
        ),
      ],
    );
  }
}