import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:gait_analysis_app/screens/home_screen.dart';
import 'package:gait_analysis_app/services/api_service.dart';
import 'package:gait_analysis_app/utils/app_theme.dart';
import 'package:gait_analysis_app/utils/constants.dart';

void main() {
  runApp(GaitAnalysisApp());
}

class GaitAnalysisApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MultiRepositoryProvider(
      providers: [
        RepositoryProvider<ApiService>(
          create: (context) => ApiService(baseUrl: AppConstants.apiBaseUrl),
        ),
      ],
      child: MaterialApp(
        title: 'MediaPipe歩行分析',
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: ThemeMode.system,
        home: HomeScreen(),
        debugShowCheckedModeBanner: false,
        localizationsDelegates: const [
          // TODO: 多言語化対応
        ],
        supportedLocales: const [
          Locale('ja', 'JP'),
          Locale('en', 'US'),
        ],
      ),
    );
  }
}