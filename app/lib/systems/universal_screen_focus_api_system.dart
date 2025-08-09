import 'package:flutter/widgets.dart';
import '../utils/app_logger.dart';

/// Configuration for a single API call that should be triggered on screen focus events
class ScreenFocusApiCall {
  final String name;
  final Future<void> Function(BuildContext context) apiCall;
  final bool runOnScreenEnter;
  final bool runOnAppResume;
  final bool oncePerSession;

  const ScreenFocusApiCall({
    required this.name,
    required this.apiCall,
    this.runOnScreenEnter = true,
    this.runOnAppResume = true,
    this.oncePerSession = true,
  });
}

/// A universal system that can execute any array of API calls when screen focus events occur
/// Replicates the exact behavior of the old rate limit system but for any API calls
class UniversalScreenFocusApiSystem {
  final List<ScreenFocusApiCall> _apiCalls = [];
  final Set<String> _callsMadeThisSession = {};
  
  bool _isActiveTab = true;
  bool _isAppActive = true;
  BuildContext? _context;
  
  final VoidCallback? onApiCallsCompleted;

  UniversalScreenFocusApiSystem({this.onApiCallsCompleted});

  /// Register a single API call
  void registerApiCall(ScreenFocusApiCall apiCall) {
    _apiCalls.add(apiCall);
    AppLogger.info('Registered API call: ${apiCall.name}');
  }

  /// Register multiple API calls that will be executed in sequence
  void registerApiCalls(List<ScreenFocusApiCall> apiCalls) {
    for (final apiCall in apiCalls) {
      registerApiCall(apiCall);
    }
  }

  /// Initialize the system - equivalent to old initState logic
  void initialize(BuildContext context, {bool isActiveTab = true}) {
    _context = context;
    _isActiveTab = isActiveTab;
    _isAppActive = true;
    _callsMadeThisSession.clear();
    
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _checkAndExecuteApiCalls();
    });
  }

  /// Equivalent to old _checkAndLoadRateLimit() but for any API calls
  void _checkAndExecuteApiCalls() {
    if (_isActiveTab && _isAppActive) {
      _executeApiCalls(trigger: 'screen_focus');
    }
  }

  /// Execute all registered API calls in sequence
  void _executeApiCalls({required String trigger}) async {
    if (_context == null) return;

    AppLogger.info('Executing ${_apiCalls.length} API calls, trigger: $trigger');

    for (final apiCall in _apiCalls) {
      bool shouldExecute = false;
      
      // Check if this call should run for this trigger
      if (trigger == 'screen_focus' || trigger == 'screen_enter') {
        shouldExecute = apiCall.runOnScreenEnter;
      } else if (trigger == 'app_resume') {
        shouldExecute = apiCall.runOnAppResume;
      }

      // Check session constraints
      if (shouldExecute && apiCall.oncePerSession) {
        shouldExecute = !_callsMadeThisSession.contains(apiCall.name);
      }

      if (shouldExecute) {
        await _executeSingleApiCall(apiCall, trigger);
      }
    }

    if (onApiCallsCompleted != null) {
      onApiCallsCompleted!();
    }
  }

  /// Execute a single API call
  Future<void> _executeSingleApiCall(ScreenFocusApiCall apiCall, String trigger) async {
    try {
      AppLogger.info('Executing API call: ${apiCall.name} (trigger: $trigger)');
      await apiCall.apiCall(_context!);
      
      if (apiCall.oncePerSession) {
        _callsMadeThisSession.add(apiCall.name);
      }
      
      AppLogger.info('API call completed: ${apiCall.name}');
    } catch (e) {
      AppLogger.warning('API call failed: ${apiCall.name} - $e');
    }
  }

  /// Equivalent to old _onTabChanged logic
  void onTabChanged(bool isActiveTab) {
    _isActiveTab = isActiveTab;
    
    if (isActiveTab) {
      // Reset session for active calls when entering the tab
      for (final apiCall in _apiCalls) {
        if (apiCall.runOnScreenEnter) {
          _callsMadeThisSession.remove(apiCall.name);
        }
      }
      _checkAndExecuteApiCalls();
    }
  }

  /// Equivalent to old didChangeAppLifecycleState logic
  void onAppLifecycleChanged(AppLifecycleState state) {
    final wasActive = _isAppActive;
    _isAppActive = state == AppLifecycleState.resumed;
    
    // If app became active and we're on active tab, execute API calls
    if (!wasActive && _isAppActive && _isActiveTab) {
      // Reset session for app resume calls
      for (final apiCall in _apiCalls) {
        if (apiCall.runOnAppResume) {
          _callsMadeThisSession.remove(apiCall.name);
        }
      }
      _executeApiCalls(trigger: 'app_resume');
    }
  }

  /// Force execute all registered API calls
  void forceExecuteAll() {
    _callsMadeThisSession.clear();
    _executeApiCalls(trigger: 'force');
  }

  /// Force execute a specific API call
  void forceExecute(String name) {
    final apiCall = _apiCalls.where((c) => c.name == name).firstOrNull;
    if (apiCall != null) {
      _callsMadeThisSession.remove(name);
      _executeSingleApiCall(apiCall, 'force');
    } else {
      AppLogger.warning('API call not found: $name');
    }
  }

  /// Get current state
  Map<String, dynamic> getState() {
    return {
      'isActiveTab': _isActiveTab,
      'isAppActive': _isAppActive,
      'registeredCalls': _apiCalls.map((c) => c.name).toList(),
      'callsMadeThisSession': _callsMadeThisSession.toList(),
    };
  }

  /// Reset session state
  void resetSession() {
    _callsMadeThisSession.clear();
  }

  /// Clear all registered API calls
  void clearApiCalls() {
    _apiCalls.clear();
    _callsMadeThisSession.clear();
  }
}

/// Mixin for widgets that want to use the UniversalScreenFocusApiSystem
mixin UniversalScreenFocusApiMixin<T extends StatefulWidget> on State<T>, WidgetsBindingObserver {
  late final UniversalScreenFocusApiSystem _apiSystem;

  /// Get the API system instance
  UniversalScreenFocusApiSystem get screenFocusApiSystem => _apiSystem;

  /// Initialize the universal screen focus API system
  void initializeScreenFocusApiSystem({bool isActiveTab = true}) {
    _apiSystem = UniversalScreenFocusApiSystem(
      onApiCallsCompleted: onScreenFocusApiCallsCompleted,
    );
    
    // Register API calls by overriding registerScreenFocusApiCalls
    registerScreenFocusApiCalls();
    
    _apiSystem.initialize(context, isActiveTab: isActiveTab);
  }

  /// Override this to register your API calls
  void registerScreenFocusApiCalls() {
    // To be implemented by the widget
  }

  /// Override this to be notified when all API calls are completed
  void onScreenFocusApiCallsCompleted() {
    // To be implemented by the widget if needed
  }

  /// Call this when tab changes
  void onScreenFocusTabChanged(bool isActiveTab) {
    _apiSystem.onTabChanged(isActiveTab);
  }

  /// Handle app lifecycle changes
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    _apiSystem.onAppLifecycleChanged(state);
  }
}
