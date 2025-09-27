/// 歩行分析データモデル

class GaitAnalysisResponse {
  final String analysisId;
  final String status;
  final DateTime timestamp;
  final double processingTimeSeconds;
  final SpatiotemporalParameters? spatiotemporalParams;
  final SymmetryIndices? symmetryIndices;
  final List<GaitCycle> gaitCycles;
  final JointAngles? jointAngles;
  final double videoQualityScore;
  final double poseDetectionConfidence;
  final int gaitCyclesDetected;
  final double overallGaitScore;
  final List<String> recommendations;
  final Map<String, dynamic> videoInfo;
  final Map<String, dynamic> analysisSettings;

  GaitAnalysisResponse({
    required this.analysisId,
    required this.status,
    required this.timestamp,
    required this.processingTimeSeconds,
    this.spatiotemporalParams,
    this.symmetryIndices,
    required this.gaitCycles,
    this.jointAngles,
    required this.videoQualityScore,
    required this.poseDetectionConfidence,
    required this.gaitCyclesDetected,
    required this.overallGaitScore,
    required this.recommendations,
    required this.videoInfo,
    required this.analysisSettings,
  });

  factory GaitAnalysisResponse.fromJson(Map<String, dynamic> json) {
    return GaitAnalysisResponse(
      analysisId: json['analysis_id'],
      status: json['status'],
      timestamp: DateTime.parse(json['timestamp']),
      processingTimeSeconds: json['processing_time_seconds'].toDouble(),
      spatiotemporalParams: json['spatiotemporal_params'] != null
          ? SpatiotemporalParameters.fromJson(json['spatiotemporal_params'])
          : null,
      symmetryIndices: json['symmetry_indices'] != null
          ? SymmetryIndices.fromJson(json['symmetry_indices'])
          : null,
      gaitCycles: (json['gait_cycles'] as List? ?? [])
          .map((x) => GaitCycle.fromJson(x))
          .toList(),
      jointAngles: json['joint_angles'] != null
          ? JointAngles.fromJson(json['joint_angles'])
          : null,
      videoQualityScore: json['video_quality_score'].toDouble(),
      poseDetectionConfidence: json['pose_detection_confidence'].toDouble(),
      gaitCyclesDetected: json['gait_cycles_detected'],
      overallGaitScore: json['overall_gait_score'].toDouble(),
      recommendations: List<String>.from(json['recommendations'] ?? []),
      videoInfo: Map<String, dynamic>.from(json['video_info'] ?? {}),
      analysisSettings: Map<String, dynamic>.from(json['analysis_settings'] ?? {}),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'analysis_id': analysisId,
      'status': status,
      'timestamp': timestamp.toIso8601String(),
      'processing_time_seconds': processingTimeSeconds,
      if (spatiotemporalParams != null)
        'spatiotemporal_params': spatiotemporalParams!.toJson(),
      if (symmetryIndices != null) 'symmetry_indices': symmetryIndices!.toJson(),
      'gait_cycles': gaitCycles.map((e) => e.toJson()).toList(),
      if (jointAngles != null) 'joint_angles': jointAngles!.toJson(),
      'video_quality_score': videoQualityScore,
      'pose_detection_confidence': poseDetectionConfidence,
      'gait_cycles_detected': gaitCyclesDetected,
      'overall_gait_score': overallGaitScore,
      'recommendations': recommendations,
      'video_info': videoInfo,
      'analysis_settings': analysisSettings,
    };
  }
}

class SpatiotemporalParameters {
  final double gaitSpeedMs;
  final int cadenceStepsPerMin;
  final double strideLengthM;
  final double strideTimeS;
  final double leftStepLengthM;
  final double rightStepLengthM;
  final double leftStanceTimeS;
  final double rightStanceTimeS;
  final double doubleSupportTimeS;

  SpatiotemporalParameters({
    required this.gaitSpeedMs,
    required this.cadenceStepsPerMin,
    required this.strideLengthM,
    required this.strideTimeS,
    required this.leftStepLengthM,
    required this.rightStepLengthM,
    required this.leftStanceTimeS,
    required this.rightStanceTimeS,
    required this.doubleSupportTimeS,
  });

  factory SpatiotemporalParameters.fromJson(Map<String, dynamic> json) {
    return SpatiotemporalParameters(
      gaitSpeedMs: json['gait_speed_ms'].toDouble(),
      cadenceStepsPerMin: json['cadence_steps_per_min'],
      strideLengthM: json['stride_length_m'].toDouble(),
      strideTimeS: json['stride_time_s'].toDouble(),
      leftStepLengthM: json['left_step_length_m'].toDouble(),
      rightStepLengthM: json['right_step_length_m'].toDouble(),
      leftStanceTimeS: json['left_stance_time_s'].toDouble(),
      rightStanceTimeS: json['right_stance_time_s'].toDouble(),
      doubleSupportTimeS: json['double_support_time_s'].toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'gait_speed_ms': gaitSpeedMs,
      'cadence_steps_per_min': cadenceStepsPerMin,
      'stride_length_m': strideLengthM,
      'stride_time_s': strideTimeS,
      'left_step_length_m': leftStepLengthM,
      'right_step_length_m': rightStepLengthM,
      'left_stance_time_s': leftStanceTimeS,
      'right_stance_time_s': rightStanceTimeS,
      'double_support_time_s': doubleSupportTimeS,
    };
  }

  /// 歩行速度を km/h に変換
  double get gaitSpeedKmh => gaitSpeedMs * 3.6;

  /// 歩行速度の評価レベル取得
  String get speedEvaluation {
    if (gaitSpeedMs >= 1.4) return '優秀';
    if (gaitSpeedMs >= 1.2) return '良好';
    if (gaitSpeedMs >= 1.0) return '普通';
    return '要改善';
  }
}

class SymmetryIndices {
  final double stepLengthSymmetryPercent;
  final double stanceTimeSymmetryPercent;
  final double swingTimeSymmetryPercent;
  final double hipFlexionSymmetryPercent;
  final double kneeFlexionSymmetryPercent;
  final double ankleFlexionSymmetryPercent;
  final double overallSymmetryScore;

  SymmetryIndices({
    required this.stepLengthSymmetryPercent,
    required this.stanceTimeSymmetryPercent,
    required this.swingTimeSymmetryPercent,
    required this.hipFlexionSymmetryPercent,
    required this.kneeFlexionSymmetryPercent,
    required this.ankleFlexionSymmetryPercent,
    required this.overallSymmetryScore,
  });

  factory SymmetryIndices.fromJson(Map<String, dynamic> json) {
    return SymmetryIndices(
      stepLengthSymmetryPercent: json['step_length_symmetry_percent'].toDouble(),
      stanceTimeSymmetryPercent: json['stance_time_symmetry_percent'].toDouble(),
      swingTimeSymmetryPercent: json['swing_time_symmetry_percent'].toDouble(),
      hipFlexionSymmetryPercent: json['hip_flexion_symmetry_percent'].toDouble(),
      kneeFlexionSymmetryPercent: json['knee_flexion_symmetry_percent'].toDouble(),
      ankleFlexionSymmetryPercent: json['ankle_dorsiflexion_symmetry_percent'].toDouble(),
      overallSymmetryScore: json['overall_symmetry_score'].toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'step_length_symmetry_percent': stepLengthSymmetryPercent,
      'stance_time_symmetry_percent': stanceTimeSymmetryPercent,
      'swing_time_symmetry_percent': swingTimeSymmetryPercent,
      'hip_flexion_symmetry_percent': hipFlexionSymmetryPercent,
      'knee_flexion_symmetry_percent': kneeFlexionSymmetryPercent,
      'ankle_dorsiflexion_symmetry_percent': ankleFlexionSymmetryPercent,
      'overall_symmetry_score': overallSymmetryScore,
    };
  }

  /// 対称性の評価レベル取得
  String get symmetryEvaluation {
    if (overallSymmetryScore >= 85) return '優秀';
    if (overallSymmetryScore >= 70) return '良好';
    if (overallSymmetryScore >= 50) return '普通';
    return '要改善';
  }
}

class GaitCycle {
  final String cycleId;
  final int startFrame;
  final int endFrame;
  final double durationSeconds;
  final String side;
  final double stepLengthM;
  final double stepWidthM;
  final double stanceTimeSeconds;
  final double swingTimeSeconds;
  final double stanceRatio;
  final double hipFlexionPeakDeg;
  final double kneeFlexionPeakDeg;
  final double ankleFlexionPeakDeg;
  final Map<String, double> phaseTimings;

  GaitCycle({
    required this.cycleId,
    required this.startFrame,
    required this.endFrame,
    required this.durationSeconds,
    required this.side,
    required this.stepLengthM,
    required this.stepWidthM,
    required this.stanceTimeSeconds,
    required this.swingTimeSeconds,
    required this.stanceRatio,
    required this.hipFlexionPeakDeg,
    required this.kneeFlexionPeakDeg,
    required this.ankleFlexionPeakDeg,
    required this.phaseTimings,
  });

  factory GaitCycle.fromJson(Map<String, dynamic> json) {
    return GaitCycle(
      cycleId: json['cycle_id'],
      startFrame: json['start_frame'],
      endFrame: json['end_frame'],
      durationSeconds: json['duration_seconds'].toDouble(),
      side: json['side'],
      stepLengthM: json['step_length_m'].toDouble(),
      stepWidthM: json['step_width_m'].toDouble(),
      stanceTimeSeconds: json['stance_time_seconds'].toDouble(),
      swingTimeSeconds: json['swing_time_seconds'].toDouble(),
      stanceRatio: json['stance_ratio'].toDouble(),
      hipFlexionPeakDeg: json['hip_flexion_peak_deg'].toDouble(),
      kneeFlexionPeakDeg: json['knee_flexion_peak_deg'].toDouble(),
      ankleFlexionPeakDeg: json['ankle_dorsiflexion_peak_deg'].toDouble(),
      phaseTimings: Map<String, double>.from(json['phase_timings'] ?? {}),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'cycle_id': cycleId,
      'start_frame': startFrame,
      'end_frame': endFrame,
      'duration_seconds': durationSeconds,
      'side': side,
      'step_length_m': stepLengthM,
      'step_width_m': stepWidthM,
      'stance_time_seconds': stanceTimeSeconds,
      'swing_time_seconds': swingTimeSeconds,
      'stance_ratio': stanceRatio,
      'hip_flexion_peak_deg': hipFlexionPeakDeg,
      'knee_flexion_peak_deg': kneeFlexionPeakDeg,
      'ankle_dorsiflexion_peak_deg': ankleFlexionPeakDeg,
      'phase_timings': phaseTimings,
    };
  }

  /// 左右識別
  bool get isLeft => side.toLowerCase() == 'left';
  bool get isRight => side.toLowerCase() == 'right';
}

class JointAngles {
  final List<double> hipFlexionDeg;
  final List<double> hipAbductionDeg;
  final List<double> kneeFlexionDeg;
  final List<double> ankleFlexionDeg;
  final List<double> pelvicDropDeg;
  final List<double> frameTimestamps;

  JointAngles({
    required this.hipFlexionDeg,
    required this.hipAbductionDeg,
    required this.kneeFlexionDeg,
    required this.ankleFlexionDeg,
    required this.pelvicDropDeg,
    required this.frameTimestamps,
  });

  factory JointAngles.fromJson(Map<String, dynamic> json) {
    return JointAngles(
      hipFlexionDeg: List<double>.from(json['hip_flexion_deg'] ?? []),
      hipAbductionDeg: List<double>.from(json['hip_abduction_deg'] ?? []),
      kneeFlexionDeg: List<double>.from(json['knee_flexion_deg'] ?? []),
      ankleFlexionDeg: List<double>.from(json['ankle_dorsiflexion_deg'] ?? []),
      pelvicDropDeg: List<double>.from(json['pelvic_drop_deg'] ?? []),
      frameTimestamps: List<double>.from(json['frame_timestamps'] ?? []),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'hip_flexion_deg': hipFlexionDeg,
      'hip_abduction_deg': hipAbductionDeg,
      'knee_flexion_deg': kneeFlexionDeg,
      'ankle_dorsiflexion_deg': ankleFlexionDeg,
      'pelvic_drop_deg': pelvicDropDeg,
      'frame_timestamps': frameTimestamps,
    };
  }

  /// ピーク値取得
  double get hipFlexionPeak => hipFlexionDeg.isNotEmpty ? hipFlexionDeg.reduce((a, b) => a > b ? a : b) : 0;
  double get kneeFlexionPeak => kneeFlexionDeg.isNotEmpty ? kneeFlexionDeg.reduce((a, b) => a > b ? a : b) : 0;
  double get ankleFlexionPeak => ankleFlexionDeg.isNotEmpty ? ankleFlexionDeg.reduce((a, b) => a > b ? a : b) : 0;

  /// 平均値取得
  double get hipFlexionMean => hipFlexionDeg.isNotEmpty ? hipFlexionDeg.reduce((a, b) => a + b) / hipFlexionDeg.length : 0;
  double get kneeFlexionMean => kneeFlexionDeg.isNotEmpty ? kneeFlexionDeg.reduce((a, b) => a + b) / kneeFlexionDeg.length : 0;
  double get ankleFlexionMean => ankleFlexionDeg.isNotEmpty ? ankleFlexionDeg.reduce((a, b) => a + b) / ankleFlexionDeg.length : 0;
}

/// 分析履歴
class GaitAnalysisHistory {
  final String analysisId;
  final DateTime timestamp;
  final double gaitSpeedMs;
  final double overallScore;
  final double symmetryScore;
  final String? notes;

  GaitAnalysisHistory({
    required this.analysisId,
    required this.timestamp,
    required this.gaitSpeedMs,
    required this.overallScore,
    required this.symmetryScore,
    this.notes,
  });

  factory GaitAnalysisHistory.fromJson(Map<String, dynamic> json) {
    return GaitAnalysisHistory(
      analysisId: json['analysis_id'],
      timestamp: DateTime.parse(json['timestamp']),
      gaitSpeedMs: json['gait_speed_ms'].toDouble(),
      overallScore: json['overall_score'].toDouble(),
      symmetryScore: json['symmetry_score'].toDouble(),
      notes: json['notes'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'analysis_id': analysisId,
      'timestamp': timestamp.toIso8601String(),
      'gait_speed_ms': gaitSpeedMs,
      'overall_score': overallScore,
      'symmetry_score': symmetryScore,
      'notes': notes,
    };
  }
}
