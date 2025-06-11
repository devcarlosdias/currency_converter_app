import 'package:currency_converter_app/features/home/presentation/widgets/calculator/number_calculator_widget.dart';
import 'package:flutter/material.dart';

class CalculatorWidget extends StatelessWidget {
  CalculatorWidget({required this.size, super.key});

  final Size size;

  final rows = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9],
    [0],
  ];

  @override
  Widget build(BuildContext context) {
    //Obtendo o espaço destinado a área dos botões e destinando 22,5% para cada faixa de botões
    final double sizeComponent = size.height * 0.225;
    //Obtendo o espaço destinado a área dos botões e destinando 3% para cada spacing entre faixa de botões, Totalizando 99% de espaço utilizado de 100%
    final double sizeSpacing = size.height * 0.03;
    return Column(
      children: [
        SizedBox(
          height: sizeComponent,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children:
                rows[0]
                    .map(
                      (e) => NumberCalculaterWidget(
                        item: e,
                        size: size.width * 0.3,
                      ),
                    )
                    .toList(),
          ),
        ),
        SizedBox(height: sizeSpacing),
        SizedBox(
          height: sizeComponent,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children:
                rows[1]
                    .map(
                      (e) => NumberCalculaterWidget(
                        item: e,
                        size: size.width * 0.3,
                      ),
                    )
                    .toList(),
          ),
        ),
        SizedBox(height: sizeSpacing),
        SizedBox(
          height: sizeComponent,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children:
                rows[2]
                    .map(
                      (e) => NumberCalculaterWidget(
                        item: e,
                        size: size.width * 0.3,
                      ),
                    )
                    .toList(),
          ),
        ),
        SizedBox(height: sizeSpacing),
        SizedBox(
          height: sizeComponent,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [NumberCalculaterWidget(item: 0, size: size.width * 0.3)],
          ),
        ),
      ],
    );
  }
}
