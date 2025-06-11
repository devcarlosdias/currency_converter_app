import 'package:currency_converter_app/features/home/presentation/widgets/calculator/calculator_widget.dart';
import 'package:currency_converter_app/theme/colors.dart';
import 'package:flutter/material.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primaryColors,
      body: SafeArea(
        top: false,
        child: Padding(
          padding: EdgeInsetsGeometry.only(
            right: 10,
            left: 10,
            bottom: 10,
            top: MediaQuery.of(context).padding.top,
          ),
          child: LayoutBuilder(
            builder:
                (context, constraints) => Column(
                  children: [
                    Container(
                      height: constraints.maxHeight * 0.08,
                      width: constraints.maxWidth,
                      color: Colors.black,
                    ),
                    SizedBox(height: constraints.maxHeight * 0.03),
                    Container(
                      height: constraints.maxHeight * 0.4,
                      width: constraints.maxWidth,
                      color: Colors.red,
                    ),
                    SizedBox(height: constraints.maxHeight * 0.03),
                    SizedBox(
                      height: constraints.maxHeight * 0.46,
                      width: constraints.maxWidth,
                      child: CalculatorWidget(
                        size: Size(
                          constraints.maxWidth,
                          constraints.maxHeight * 0.46,
                        ),
                      ),
                    ),
                  ],
                ),
          ),
        ),
      ),
    );
  }
}
