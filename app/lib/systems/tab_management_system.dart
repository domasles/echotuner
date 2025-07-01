import 'package:flutter/material.dart';

class TabManagementSystem {
    TabController? _tabController;
    Function()? _refreshCallback;
    bool _showTabsDuringLoading = true;
    
    TabController? get tabController => _tabController;
    bool get showTabsDuringLoading => _showTabsDuringLoading;

    void initialize({required int tabCount, required TickerProvider vsync, Function()? onTabChanged, bool showTabsDuringLoading = true}) {
        _tabController = TabController(length: tabCount, vsync: vsync);
        _refreshCallback = onTabChanged;
        _showTabsDuringLoading = showTabsDuringLoading;

        _tabController!.addListener(() {
            if (!_tabController!.indexIsChanging && _refreshCallback != null) {
                _refreshCallback!();
            }
        });
    }

    void dispose() {
        _tabController?.dispose();
    }

    void setRefreshCallback(Function() callback) {
        _refreshCallback = callback;
    }

    int get currentIndex => _tabController?.index ?? 0;
    
    void animateToTab(int index) {
        _tabController?.animateTo(index);
    }
}

mixin TabManagementMixin on State, TickerProviderStateMixin {
    final TabManagementSystem _tabSystem = TabManagementSystem();
    TabController? get tabController => _tabSystem.tabController;
    
    void initializeTabSystem({required int tabCount, Function()? onTabChanged, bool showTabsDuringLoading = true}) {
        _tabSystem.initialize(
            tabCount: tabCount,
            vsync: this,
            onTabChanged: onTabChanged ?? _defaultRefreshHandler,
            showTabsDuringLoading: showTabsDuringLoading,
        );
    }

    void _defaultRefreshHandler() {
        if (mounted) {
            refreshCurrentTab();
        }
    }

    void refreshCurrentTab() {
    }

    @override
    void dispose() {
        _tabSystem.dispose();
        super.dispose();
    }

    int get currentTabIndex => _tabSystem.currentIndex;

    void switchToTab(int index) {
        _tabSystem.animateToTab(index);
    }

    Widget buildTabBarView({required List<Widget> children, bool isLoading = false, Widget? loadingWidget}) {
        if (isLoading && !_tabSystem.showTabsDuringLoading) {
            return loadingWidget ?? const Center(child: CircularProgressIndicator());
        }

        return TabBarView(
            controller: _tabSystem.tabController,
            children: children,
        );
    }

    Widget buildTabBar({required List<Widget> tabs, bool isLoading = false}) {
        if (isLoading && !_tabSystem.showTabsDuringLoading) {
            return const SizedBox.shrink();
        }

        return TabBar(
            controller: _tabSystem.tabController,
            tabs: tabs,
        );
    }
}
