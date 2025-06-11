
import 'package:flutter/material.dart';

class NumberCalculaterWidget extends StatelessWidget {
  const NumberCalculaterWidget({
    required this.item,
    required this.size,
    super.key,
  });

  final int item;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      //decoration: BoxDecoration(shape: BoxShape.circle, color: Color(0XFF36c665)),
      decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.white.withOpacity(0.1)),
      height: size,
      width: size,
      alignment: Alignment.center,
      child: Text(item.toString(), style: TextStyle(
        color: Colors.white,
        fontWeight: FontWeight.bold,
        fontSize: size * 0.2
      ),),
    );
  }
}
